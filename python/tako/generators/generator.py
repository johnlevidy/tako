# Copyright 2020 Jacob Glueck
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import typing as t

import abc
import argparse
from tako.util.qname import QName
from pathlib import Path
from tako.core import sir


class Generator(abc.ABC):
    @abc.abstractmethod
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        ...

    @abc.abstractmethod
    def generate_into(self, proto: sir.Protocol, out_dir: Path, args: t.Any) -> None:
        ...

    @abc.abstractmethod
    def list_outputs(
        self, proto_qname: QName, args: t.Any
    ) -> t.Generator[Path, None, None]:
        ...

    def generate(self, proto: sir.Protocol, out_dir: Path, args: t.Any) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        self.generate_into(proto, out_dir, args)
