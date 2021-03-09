// Copyright 2020 Jacob Glueck
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package tako;

import java.nio.ByteBuffer;
import tako.TakoType;
import tako.ParseException;

public interface SimpleTakoType<Rendered, Built> extends TakoType<Rendered, Built> {
    void render(Rendered out, ByteBuffer buf, int offset);
    // Returns the new offset
    int parse(Rendered out, ByteBuffer buf, int offset) throws ParseException;
}
