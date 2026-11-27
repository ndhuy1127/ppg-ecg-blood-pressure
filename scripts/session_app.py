"""Session app, recording screen (docs/protocol/session_app_spec_v0.md, section 6).

Two modes, both outside data/raw/ (participant mode comes with the preparation
screen, spec step 5):

- ``--demo``: a SYNTHETIC device (software/session_app/fake_device.py) plays a
  stream and answers the marks; a "board t0" button stands for SW1. For trying
  the app; the output is SYNTHETIC.
- ``--port COM5 --metadata <bring-up metadata>``: runs ``packet_logger.py record
  --commands --stop-file`` as a child process (the only writer of raw.bin), reads
  raw.bin while it grows, and sends marks through the recording's command inbox.

The rules (attempts, repeats, caps, safety) are those of
software/session_app/visit.py; this file only draws and wires. Every step goes to
``session_journal.jsonl`` as it happens; at the end the cuff log (cuff-log-v2)
and the list of exceptions are written. Nothing is overwritten.

    python scripts/session_app.py --demo
    python scripts/session_app.py --port COM5 --metadata <metadata.json>
"""

import argparse
import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from software.device.session_ingest import CUFF_COLUMNS_V2  # noqa: E402
from software.session_app.live import LiveStream, display_points, y_limits  # noqa: E402
from software.session_app.visit import (  # noqa: E402
    PHASES,
    REPEAT_REASONS,
    SCREEN,
    NeedsConfirmation,
    Visit,
    VisitError,
)

CONFIG = REPO / "configs/session_app/session_app_v0.json"
# Operator wording of the rule messages of software/session_app/visit.py (which
# stay English, like the rest of the code and the journal).
VIETNAMESE = (
    (r"attempt (\w+) is still open",
     r"Lượt \1 vẫn đang mở: lưu nhãn hoặc hủy lượt đó trước khi bắt đầu lượt mới."),
    (r"the session was stopped", "Buổi đo đã dừng."),
    (r"(\S+) was stopped", r"Nghiệm pháp \1 đã dừng."),
    (r"(\S+) is not done in this session.*",
     r"Buổi này không làm \1 (chỉ đo M0, hoặc trung bình M0 từ 140/90 trở lên)."),
    (r"rest at least (\S+) s between inflations \((\S+) s so far\)",
     r"Phải nghỉ ít nhất \1 s giữa hai lần bơm (mới được \2 s)."),
    (r"inflation cap (\S+) reached", r"Đã đủ trần \1 lần bơm của buổi."),
    (r"screening inflations only in session 1", "Đo hai tay khi sàng lọc chỉ có ở buổi 1."),
    (r"both screening inflations are done", "Đã đo đủ hai lần sàng lọc."),
    (r"screening inflations are not repeated", "Lần đo sàng lọc không đo lại."),
    (r"only M1 or M2 can be stopped on its own",
     "Chỉ dừng riêng được M1 hoặc M2; muốn dừng hết thì bấm DỪNG BUỔI."),
    (r"every (\S+) slot has its scheduled attempt.*",
     r"Các vị trí \1 đã có lượt theo lịch; muốn đo lại thì dùng nút Đo lại lượt."),
    (r"repeats only at.*", "Chỉ được đo lại ở M0."),
    (r"repeat reason must be.*", "Lý do đo lại phải là no_result hoặc observed_motion."),
    (r"(\S+) is not a labelled (\S+) attempt",
     r"\1 không phải một lượt \2 đã có nhãn (nhập mã lượt, ví dụ E01)."),
    (r"a device error stops the session; no repeat",
     "Máy cuff lỗi thì dừng buổi, không đo lại."),
    (r"(\S+) is already repeated", r"\1 đã được đo lại rồi."),
    (r"(\S+) has a result \((\w+)\)",
     r"\1 đã có kết quả (\2), không đo lại với lý do no_result."),
    (r"no motion was marked before the t0 of (\S+)",
     r"Không có đánh dấu cử động trước t0 của \1, nên không đo lại vì cử động."),
    (r"at most (\S+) repeats per session", r"Mỗi buổi đo lại tối đa \1 lần."),
    (r"no open attempt", "Chưa có lượt nào đang mở: bấm Bắt đầu lượt trước."),
    (r"no t0 to withdraw", "Lượt đang mở chưa có t0 để bỏ."),
    (r"a reason is needed", "Cần ghi lý do."),
    (r"(\S+) must be an integer", r"\1 phải là số nguyên."),
    (r"DBP must be below SBP", "DBP phải nhỏ hơn SBP."),
    (r"only a valid result carries SBP/DBP",
     "Chỉ kết quả valid mới có SBP/DBP; với no_result hay device_error để trống hai ô."),
    (r"t0 was more than (\S+) s off the plan.*",
     r"Bấm cuff lệch kế hoạch quá \1 s: ghi vào ô Lý do lệch giờ."),
    (r"t0 is the SW1 button on the base board", "t0 là nút SW1 trên bo đế."),
    (r".*command_inbox\.jsonl not found.*",
     "Logger chưa sẵn sàng nhận lệnh. Chờ vài giây sau khi bắt đầu ghi rồi thử lại."),
    (r"invalid literal for int\(\).*", "Các ô số chỉ nhận số nguyên."),
)


def vietnamese(message):
    """The operator wording of a rule message; unknown messages pass unchanged."""
    import re

    for pattern, text in VIETNAMESE:
        if re.fullmatch(pattern, message):
            return re.sub(pattern, text, message)
    return message
MARK_CODES = {"operator": 4, "cuff_end": 2}
EVENT_TYPES = ("ho", "nói", "chỉnh dây", "cử động khác", "khác")


class DemoLink:
    """The SYNTHETIC device of the demo mode; also keeps the bytes it played."""

    demo = True

    def __init__(self, folder, minutes):
        from software.session_app.fake_device import FakeDevice

        self.device = FakeDevice(duration_s=minutes * 60.0)
        self.raw = open(folder / "raw_demo.bin", "xb")
        self.started = time.monotonic()
        self.recording = "demo"

    def now(self):
        return time.monotonic() - self.started

    def read(self):
        data = self.device.read(self.now())
        self.raw.write(data)
        return data

    def mark(self, event):
        self.device.event(MARK_CODES[event], self.now())

    def board_t0(self):
        self.device.event(1, self.now())

    def alive(self):
        return True

    def messages(self):
        return []

    def stop(self):
        self.raw.close()
        return "demo stopped"


class LoggerLink:
    """``packet_logger.py record`` as a child process (spec section 3)."""

    demo = False

    def __init__(self, folder, port, metadata, duration_s):
        self.recording_dir = folder / "recording"
        self.stop_file = folder / "stop_request"
        self.recording = self.recording_dir.name
        command = [sys.executable, str(REPO / "scripts/packet_logger.py"), "record",
                   "--port", port, "--duration-s", str(duration_s), "--commands",
                   "--metadata", str(metadata), "--output", str(self.recording_dir),
                   "--stop-file", str(self.stop_file), "--compress-tables"]
        # The logger writes its console to a file, not to a pipe of this window:
        # if the window dies, the logger still ends normally and writes its
        # manifest (a pipe to a dead reader broke that on 2026-11-27).
        self.console = folder / "logger_console.txt"
        with open(self.console, "x", encoding="utf-8") as out:
            self.process = subprocess.Popen(
                command, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.console_offset = 0
        self.offset = 0
        self.started = time.monotonic()

    def alive(self):
        return self.process.poll() is None

    def now(self):
        return time.monotonic() - self.started

    def read(self):
        raw = self.recording_dir / "raw.bin"
        if not raw.exists():
            return b""
        with open(raw, "rb") as handle:   # read-only, next to the logger's "xb"
            handle.seek(self.offset)
            data = handle.read()
        self.offset += len(data)
        return data

    def mark(self, event):
        from scripts.device_command import queue_command

        queue_command(self.recording_dir, {"cmd": "mark_event", "event": event})

    def board_t0(self):
        raise RuntimeError("t0 is the SW1 button on the base board")

    def messages(self):
        """New lines of the logger console since the last call."""
        with open(self.console, "rb") as handle:
            handle.seek(self.console_offset)
            data = handle.read()
        cut = data.rfind(b"\n") + 1      # keep a half-written line for next time
        self.console_offset += cut
        text = data[:cut].decode("utf-8", errors="replace")
        return [line.rstrip() for line in text.splitlines() if line.strip()]

    def stop(self):
        """Stop file, then wait for the logger to write its manifest (spec 3.2)."""
        if self.process.poll() is None:
            self.stop_file.write_text("stop\n", encoding="utf-8")
            try:
                self.process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                return "logger did not stop within 120 s"
        manifest = (self.recording_dir / "session_manifest.json").exists()
        return (f"logger exit code {self.process.returncode}, manifest "
                f"{'written' if manifest else 'MISSING'}")


class SessionCore:
    """What the screen does, without dialogs (tested headless)."""

    def __init__(self, link, visit, folder):
        self.link, self.visit, self.folder = link, visit, folder
        self.live = LiveStream()
        self.journal_file = open(folder / "session_journal.jsonl", "x", encoding="utf-8")
        self.written = 0
        self.log_lines = []
        self.flush()

    def flush(self):
        for entry in self.visit.journal[self.written:]:
            self.journal_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.written = len(self.visit.journal)
        self.journal_file.flush()

    def tick(self):
        now = self.link.now()
        for item in self.live.feed(self.link.read()):
            if item[0] == "session":
                self.visit.device_session(item[1], now)
            elif item[0] == "event":
                self.visit.device_event(item[1], item[2], now)
        self.log_lines.extend(self.link.messages())
        self.flush()
        return now

    def act(self, name, *args, **kwargs):
        """One visit operation at the current time; the journal is written at once."""
        try:
            return getattr(self.visit, name)(*args, now=self.link.now(), **kwargs)
        finally:
            self.flush()

    def mark(self, kind, **fields):
        """A code-4 mark: the visit queues it, then the device gets the command."""
        if kind == "motion":
            counted = self.act("mark_motion", note=fields.get("note", ""))
            if counted:
                self.link.mark("operator")
            return counted
        self.act("send_mark", kind, **fields)
        self.link.mark("operator")
        return True

    def finish(self, led_readjusted=0, pilot=0):
        """Stop the source and write the cuff log and the exceptions (new files)."""
        status = self.link.stop()
        self.visit._log("recording_stopped", self.link.now(), result=status)
        self.flush()
        self.journal_file.close()
        rows = self.visit.cuff_log_rows(led_readjusted, pilot)
        recording = self.link.recording
        for row in rows:
            row["recording"] = row["recording"] or recording
        with open(self.folder / "cuff_log.csv", "x", newline="", encoding="utf-8") as h:
            writer = csv.DictWriter(h, fieldnames=CUFF_COLUMNS_V2, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with open(self.folder / "exceptions.json", "x", encoding="utf-8") as h:
            json.dump(self.visit.exceptions(), h, indent=2, ensure_ascii=False)
        return status, len(rows)

    def discard(self):
        """End a trial without keeping it: stop the source, then delete this run's
        folder. Only demo and bring-up runs under runs/session_app/ (spec section 2,
        point 1 keeps every byte of participant data; there is no participant mode
        here yet, and this refuses any folder elsewhere)."""
        import shutil

        base = (REPO / "runs/session_app").resolve()
        folder = self.folder.resolve()
        if base not in folder.parents or self.visit.subject_id not in ("SYN_DEMO",
                                                                         "BRINGUP"):
            raise ValueError("Chỉ bỏ được bản thử Demo hay Bring-up trong runs/session_app/")
        status = self.link.stop()
        self.journal_file.close()
        shutil.rmtree(folder)
        return status


def build_window(core, root):  # pragma: no cover - drawing only
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk

    import matplotlib
    import numpy as np

    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    visit = core.visit
    root.title(f"Buổi đo {visit.subject_id} {visit.session_id}"
               + (" — DEMO (SYNTHETIC)" if core.link.demo else " — bring-up"))
    root.configure(background="#fff7d6" if core.link.demo else "#eef3ff")
    root.minsize(1366, 768)

    left = ttk.Frame(root, padding=6)
    left.pack(side="left", fill="y")
    right = ttk.Frame(root, padding=6)
    right.pack(side="right", fill="both", expand=True)

    status = tk.StringVar()
    ttk.Label(right, textvariable=status, font=("Segoe UI", 11), justify="left").pack(
        anchor="w")
    figure = Figure(figsize=(9, 6), dpi=90)
    axes = figure.subplots(4, 1, sharex=True)
    names = ("ECG", "PPG xanh", "PPG đỏ / IR", "|gia tốc|")
    lines = []
    for ax, name in zip(axes, names):
        ax.set_ylabel(name, fontsize=8)
        lines.append(ax.plot([], [], lw=0.8)[0])
    lines.append(axes[2].plot([], [], lw=0.8)[0])
    axes[-1].set_xlabel("giây (0 = bây giờ)")
    canvas = FigureCanvasTkAgg(figure, master=right)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def warn(exc):
        messagebox.showwarning("Không làm được", vietnamese(str(exc)))

    def guarded(action):
        def run():
            try:
                action()
            except (VisitError, RuntimeError, FileNotFoundError, ValueError) as exc:
                warn(exc)
        return run

    def section(text):
        ttk.Label(left, text=text, font=("Segoe UI", 10, "bold")).pack(anchor="w",
                                                                         pady=(8, 2))

    section("Lượt cuff")
    phase = tk.StringVar(value="M0")
    ttk.Combobox(left, textvariable=phase, values=(*PHASES, SCREEN), width=8,
                 state="readonly").pack(anchor="w")
    ttk.Button(left, text="Bắt đầu lượt", command=guarded(
        lambda: core.act("open", phase.get()))).pack(fill="x")
    parent, reason = tk.StringVar(), tk.StringVar(value=REPEAT_REASONS[0])
    row = ttk.Frame(left)
    row.pack(fill="x")
    ttk.Entry(row, textvariable=parent, width=6).pack(side="left")
    ttk.Combobox(row, textvariable=reason, values=REPEAT_REASONS, width=14,
                 state="readonly").pack(side="left")
    ttk.Button(left, text="Đo lại lượt (chỉ M0)", command=guarded(
        lambda: core.act("open", "M0", repeat_of=parent.get().strip().upper(),
                         repeat_reason=reason.get()))).pack(fill="x")
    ttk.Button(left, text="Cử động (trước t0)", command=guarded(
        lambda: core.mark("motion"))).pack(fill="x")
    if core.link.demo:
        ttk.Button(left, text="[demo] Nút t0 trên bo", command=guarded(
            core.link.board_t0)).pack(fill="x")
    ttk.Button(left, text="CUFF XẢ XONG", command=guarded(
        lambda: core.link.mark("cuff_end"))).pack(fill="x", ipady=6)
    ttk.Button(left, text="Máy đã ra kết quả", command=guarded(
        lambda: core.act("result_shown"))).pack(fill="x")

    section("Nghiệm pháp")
    ttk.Button(left, text="Bắt đầu thở chậm (M1)", command=guarded(
        lambda: core.mark("phase_M1"))).pack(fill="x")

    def m2():
        number = simpledialog.askinteger("M2", "Số bắt đầu đã đọc:", parent=root)
        if number is not None:
            core.mark("phase_M2", start_number=number)
    ttk.Button(left, text="Đọc số bắt đầu (M2)", command=guarded(m2)).pack(fill="x")

    def event():
        kind = simpledialog.askstring("Sự kiện", f"Loại ({', '.join(EVENT_TYPES)}):",
                                      parent=root)
        if kind:
            core.mark("event", event_type=kind)
    ttk.Button(left, text="Sự kiện", command=guarded(event)).pack(fill="x")

    section("Nhãn từ máy cuff")
    result = tk.StringVar(value="valid")
    for value in ("valid", "no_result", "device_error"):
        ttk.Radiobutton(left, text=value, value=value, variable=result).pack(anchor="w")
    fields = {}
    for key, text in (("sbp", "SBP"), ("dbp", "DBP"), ("pulse", "Mạch"),
                      ("note", "Ghi chú"), ("deviation", "Lý do lệch giờ")):
        row = ttk.Frame(left)
        row.pack(fill="x")
        ttk.Label(row, text=text, width=13).pack(side="left")
        fields[key] = tk.StringVar()
        ttk.Entry(row, textvariable=fields[key], width=10).pack(side="left")

    def number(key):
        text = fields[key].get().strip()
        return int(text) if text else None

    def save_label():
        args = dict(sbp=number("sbp"), dbp=number("dbp"), pulse=number("pulse"),
                    note=fields["note"].get(),
                    deviation_reason=fields["deviation"].get().strip() or None)
        try:
            actions = core.act("label", result.get(), **args)
        except NeedsConfirmation as exc:
            if not messagebox.askyesno("Xác nhận", f"{exc}\nGiữ đúng số đã nhập?"):
                return
            actions = core.act("label", result.get(), confirm=True, **args)
        for field in fields.values():
            field.set("")
        if "stop_visit" in actions and messagebox.askyesno(
                "An toàn", "Số đo ≥ 180/110 hoặc máy cuff lỗi: dừng buổi đo theo tài "
                           "liệu an toàn mục 4, 6?"):
            core.act("stop_visit", reason="safety rule (a) or device error")
        if "skip_maneuvers" in actions:
            messagebox.showinfo("An toàn", "Trung bình M0 ≥ 140/90: không làm M1, M2.")
    ttk.Button(left, text="Lưu nhãn", command=guarded(save_label)).pack(fill="x")

    section("Sửa và dừng")

    def with_reason(title, action):
        def run():
            text = simpledialog.askstring(title, "Lý do:", parent=root)
            if text:
                action(text)
        return guarded(run)
    ttk.Button(left, text="t0 nhầm", command=with_reason(
        "t0 nhầm", lambda r: core.act("false_t0", reason=r))).pack(fill="x")
    ttk.Button(left, text="Hủy lượt (không nhãn)", command=with_reason(
        "Hủy lượt", lambda r: core.act("abort", reason=r))).pack(fill="x")
    for name in ("M1", "M2"):
        ttk.Button(left, text=f"Dừng nghiệm pháp {name}", command=with_reason(
            f"Dừng {name}", lambda r, n=name: core.act("stop_maneuver", n, reason=r))).pack(
            fill="x")
    ttk.Button(left, text="DỪNG BUỔI", command=with_reason(
        "Dừng buổi", lambda r: core.act("stop_visit", reason=r))).pack(fill="x", ipady=6)

    def finish():
        # Demo and bring-up runs may be dropped (a trial of the app); a participant
        # session will only offer to save (spec section 2, point 1).
        answer = messagebox.askyesnocancel(
            "Kết thúc", "Dừng ghi. Lưu lần chạy này?\n\n"
                        "Yes: lưu nhật ký buổi, nhật ký cuff và bản ghi.\n"
                        "No: không lưu, xóa toàn bộ thư mục của lần chạy thử này.\n"
                        "Cancel: quay lại, tiếp tục ghi.")
        if answer is None:
            return
        if answer:
            result_text, n = core.finish()
            messagebox.showinfo("Đã lưu",
                                f"{result_text}\n{n} dòng nhật ký cuff\n{core.folder}")
        else:
            if not messagebox.askyesno("Không lưu", f"Xóa hẳn thư mục\n{core.folder}?\n"
                                                    "Không lấy lại được."):
                return
            core.discard()
        root.destroy()
    ttk.Button(left, text="Kết thúc ghi", command=guarded(finish)).pack(fill="x",
                                                                       pady=(10, 0))
    # The window's X button ends the recording the same way: a logger left running
    # keeps the port and never writes its manifest (2026-11-27).
    root.protocol("WM_DELETE_WINDOW", guarded(finish))
    banner = tk.Label(right, text="", foreground="white", background="#b00020",
                      font=("Segoe UI", 12, "bold"))
    warned = [False]

    # Drawing: about 10 frames a second with at most ~1200 points a trace (min-max
    # per bucket keeps the peaks); the Y range follows the data once a second so
    # the traces do not jump on every frame (review of the lag, 2026-11-27).
    last_draw, last_scale = [0.0], [0.0]
    axes[0].set_xlim(-core.live.window_s, 0)
    owner = (0, 1, 2, 3, 2)  # axis of each line (red and IR share one)

    def refresh():
        now = core.tick()
        if now - last_draw[0] >= 0.1:
            last_draw[0] = now
            traces = (core.live.trace(0xE1), core.live.trace(0xF1),
                      core.live.trace(0xF2), core.live.acc_magnitude(),
                      core.live.trace(0xF3))
            for line, (x, y) in zip(lines, traces):
                line.set_data(*display_points(x, y))
            if now - last_scale[0] >= 1.0:
                last_scale[0] = now
                for n, ax in enumerate(axes):
                    data = [traces[i][1] for i, a in enumerate(owner) if a == n]
                    limits = y_limits(np.concatenate(data)) if data else None
                    if limits is not None:
                        ax.set_ylim(*limits)
            canvas.draw_idle()
        attempt = visit.open_attempt
        text = [f"{now / 60:5.1f} phút   lần bơm {visit.inflations()}/{visit.cap()}   "
                f"gói mất {sum(core.live.lost.values())}"
                + (f" (+{sum(core.live.lost_overflow.values())} lúc bắt đầu: bộ đệm MCU "
                   "tràn khi chưa có ai đọc cổng)" if core.live.lost_overflow else "")
                + f"   LED {core.live.led}",
                "lượt mở: " + (f"{attempt.key} {attempt.phase}"
                               f"{' t0' if attempt.t0_s is not None else ''}"
                               f"{' cuff_end' if attempt.cuff_end_s is not None else ''}"
                               if attempt else "không")]
        if core.live.status_seen:
            text.append(f"STATUS: {core.live.status_seen}")
        for kind, value in visit.reminders(now):
            text.append(f"NHẮC: {kind} {value if value is not None else ''}")
        if visit.stopped:
            text.append(f"BUỔI ĐÃ DỪNG: {visit.stopped}")
        text.extend(core.log_lines[-3:])
        status.set("\n".join(text))
        if not core.link.alive() and not warned[0]:
            warned[0] = True
            banner.configure(text="LOGGER ĐÃ DỪNG: không còn dữ liệu mới. Xem dòng log ở "
                                  "trên, bấm Kết thúc ghi rồi mở lại.")
            banner.pack(fill="x", before=canvas.get_tk_widget())
        root.after(50, refresh)

    refresh()


SETTINGS = REPO / "runs/session_app/settings.json"
# Spec 10.1, point 19: participant mode opens only when these exist (none yet).
PARTICIPANT_NEEDS = ("checklist đã được hội đồng duyệt", "danh sách người trực",
                     "hash firmware nghiên cứu", "dải ADC đã chọn (SPO2_ADC_RGE)",
                     "model máy cuff")


def serial_ports():
    """(device, description) of the serial ports Windows sees now."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    return sorted((p.device, p.description or "") for p in list_ports.comports())


def load_settings():
    """Last choices of this computer (port, metadata file); a convenience only."""
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(values):
    try:
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(json.dumps(values, indent=2), encoding="utf-8")
    except OSError:
        pass


def check_port(port):
    """Open and close ``port`` once (DTR/RTS deasserted, like the logger) so a port
    held by another program is reported before anything starts."""
    from scripts.packet_logger import open_serial

    try:
        handle = open_serial(port, 115200)
    except Exception as exc:  # noqa: BLE001 - shown to the operator as is
        held = "PermissionError" in repr(exc) or "Access is denied" in str(exc)
        raise ValueError(
            f"Không mở được cổng {port}"
            + (": cổng đang bị một chương trình khác giữ (một lần ghi trước chưa dừng, "
               "trang live_viewer hay PlatformIO monitor). Đóng chương trình đó rồi thử "
               "lại." if held else f": {exc}")) from None
    handle.close()


def start_session(mode, session="S001", m0_only=False, port=None, metadata=None,
                  demo_minutes=15.0, output=None):
    """Make the folder, the visit and the source; returns the SessionCore."""
    if mode not in ("demo", "bringup"):
        raise ValueError("mode is demo or bringup (participant mode is not open yet)")
    if mode == "bringup" and (not port or metadata is None):
        raise ValueError("bring-up needs a serial port and a metadata file")
    if mode == "bringup" and not Path(metadata).is_file():
        raise ValueError(f"metadata file not found: {metadata}")
    if mode == "bringup":
        check_port(port)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = Path(output) if output else REPO / "runs/session_app" / f"{stamp}_{mode}"
    folder.mkdir(parents=True, exist_ok=False)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    visit = Visit("SYN_DEMO" if mode == "demo" else "BRINGUP", session, config,
                  m0_only=m0_only)
    if mode == "demo":
        link = DemoLink(folder, demo_minutes)
    else:
        link = LoggerLink(folder, port, metadata,
                          config["reminders_s"]["visit_cap"] + 600)
    visit.start(link.now())
    visit.recording_started(link.recording, link.now())
    return SessionCore(link, visit, folder)


def build_start_screen(root, on_start):  # pragma: no cover - drawing only
    """The first screen: mode, serial port (found automatically), metadata,
    session. ``on_start(options)`` gets the choices when "Bắt đầu" is pressed."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    settings = load_settings()
    root.title("Ứng dụng buổi đo")
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    big = ("Segoe UI", 12)
    ttk.Label(frame, text="Ứng dụng buổi đo", font=("Segoe UI", 18, "bold")).pack(
        anchor="w", pady=(0, 12))

    ttk.Label(frame, text="Chế độ", font=big).pack(anchor="w")
    mode = tk.StringVar(value=settings.get("mode", "demo"))
    ttk.Radiobutton(frame, text="Demo: dữ liệu giả lập, không cần thiết bị", value="demo",
                    variable=mode).pack(anchor="w")
    ttk.Radiobutton(frame, text="Bring-up: thiết bị thật trên bàn, chưa có người tham gia",
                    value="bringup", variable=mode).pack(anchor="w")
    ttk.Radiobutton(frame, text="Người tham gia (chưa mở được)", value="participant",
                    variable=mode, state="disabled").pack(anchor="w")
    ttk.Label(frame, foreground="#666", wraplength=640, justify="left",
              text="Chế độ người tham gia mở khi đủ: " + "; ".join(PARTICIPANT_NEEDS)
              + ".").pack(anchor="w", pady=(0, 10))

    ttk.Label(frame, text="Cổng thiết bị", font=big).pack(anchor="w")
    row = ttk.Frame(frame)
    row.pack(fill="x")
    port = tk.StringVar()
    ports = ttk.Combobox(row, textvariable=port, width=50, state="readonly")
    ports.pack(side="left")
    found = tk.StringVar()

    def rescan():
        items = [f"{device} — {description}" for device, description in serial_ports()]
        ports["values"] = items
        last = settings.get("port")
        chosen = next((i for i in items if last and i.startswith(last + " ")), None)
        port.set(chosen or (items[0] if items else ""))
        found.set(f"Tìm thấy {len(items)} cổng." if items else
                  "Chưa thấy cổng nào: kiểm tra cáp USB (cáp có truyền dữ liệu), cắm vào "
                  "cổng USB nối thẳng ESP32-S3, rồi bấm Dò lại.")
    ttk.Button(row, text="Dò lại", command=rescan).pack(side="left", padx=6)
    ttk.Label(frame, textvariable=found, foreground="#a33", wraplength=640).pack(
        anchor="w", pady=(0, 10))
    rescan()

    ttk.Label(frame, text="File metadata của bản ghi (bring-up)", font=big).pack(anchor="w")
    row = ttk.Frame(frame)
    row.pack(fill="x", pady=(0, 10))
    metadata = tk.StringVar(value=settings.get("metadata", ""))
    ttk.Entry(row, textvariable=metadata, width=60).pack(side="left")

    def browse():
        path = filedialog.askopenfilename(title="Chọn metadata", parent=root,
                                          filetypes=[("JSON", "*.json")])
        if path:
            metadata.set(path)
    ttk.Button(row, text="Chọn…", command=browse).pack(side="left", padx=6)

    ttk.Label(frame, text="Buổi", font=big).pack(anchor="w")
    row = ttk.Frame(frame)
    row.pack(fill="x", pady=(0, 16))
    session = tk.StringVar(value="S001")
    for value, text in (("S001", "Buổi 1"), ("S002", "Buổi 2")):
        ttk.Radiobutton(row, text=text, value=value, variable=session).pack(side="left")
    m0_only = tk.BooleanVar(value=False)
    ttk.Checkbutton(row, text="Chỉ đo M0", variable=m0_only).pack(side="left", padx=20)

    def start():
        options = {"mode": mode.get(), "session": session.get(), "m0_only": m0_only.get()}
        if options["mode"] == "bringup":
            if not port.get():
                messagebox.showwarning("Thiếu cổng", found.get() or "Chọn cổng thiết bị.")
                return
            options["port"] = port.get().split(" — ")[0]
            options["metadata"] = metadata.get().strip()
        save_settings({"mode": options["mode"], "port": options.get("port"),
                       "metadata": options.get("metadata", metadata.get())})
        try:
            on_start(options)
        except (ValueError, OSError) as exc:
            messagebox.showwarning("Chưa bắt đầu được", str(exc))
            return
        frame.destroy()
    ttk.Button(frame, text="Bắt đầu", command=start).pack(anchor="w", ipadx=20, ipady=6)
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--demo", action="store_true", help="SYNTHETIC device")
    parser.add_argument("--demo-minutes", type=float, default=15.0)
    parser.add_argument("--port", help="Serial port of the device (bring-up)")
    parser.add_argument("--metadata", type=Path, help="Bring-up session metadata")
    parser.add_argument("--session", default="S001", choices=("S001", "S002"))
    parser.add_argument("--m0-only", action="store_true")
    parser.add_argument("--output", type=Path, help="New folder (default runs/session_app/)")
    args = parser.parse_args()
    if args.demo and args.port:
        parser.error("choose --demo or --port")
    import tkinter as tk

    root = tk.Tk()
    if not args.demo and not args.port:
        # No arguments (the desktop icon): the start screen asks for everything.
        build_start_screen(root, lambda options: build_window(
            start_session(**options), root))
    else:
        if args.port and args.metadata is None:
            parser.error("--port needs --metadata")
        core = start_session("demo" if args.demo else "bringup", args.session,
                             args.m0_only, args.port, args.metadata, args.demo_minutes,
                             args.output)
        build_window(core, root)
    root.mainloop()


if __name__ == "__main__":
    main()
