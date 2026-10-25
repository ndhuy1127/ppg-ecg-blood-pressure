# Mã của bên thứ ba trong firmware

## Bosch Sensortec BMI270_SensorAPI (cấu hình microcode BMI270)

- File: [drivers/bmi270_config.c](drivers/bmi270_config.c), chỉ mảng
  `bmi270_config_file` (8192 byte), chép nguyên từ `bmi270.c` v2.86.1.
- Nguồn: <https://github.com/boschsensortec/BMI270_SensorAPI>, commit
  `41129fcfe39c583ee5462d79195741945d51c1fe`; SHA-256 của mảng
  `2d75e68e343a13ff99be98261dfbd99d9e8c6f267da9e3c5aeb883276ad178db`.
- Giấy phép: BSD-3-Clause. Bản firmware đã build (nhị phân) chứa mảng này nên
  phải kèm thông báo dưới đây.

```text
Copyright (c) 2023 Bosch Sensortec GmbH. All rights reserved.

BSD-3-Clause

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```
