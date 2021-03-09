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

import re

# camelCase
# snake_case
# PascalCase


def snake_to_pascal(name: str) -> str:
    return "".join([x.capitalize() for x in name.split("_")])


pascal_to_snake_regex = re.compile(r"(?<!^)(?=[A-Z])")


def pascal_to_snake(name: str) -> str:
    return pascal_to_snake_regex.sub("_", name).lower()


def snake_to_camel(name: str) -> str:
    return lower_first(snake_to_pascal(name))


def lower_first(x: str) -> str:
    return x[0].lower() + x[1:]
