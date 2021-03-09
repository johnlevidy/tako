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

public interface TakoType<Rendered, Built> {
    Rendered newRendered();
    Built newBuilt();

    void build(Built out, Rendered rendered);
    // Returns the new offset
    int serializeInto(Built built, ByteBuffer buf, int offset);
    int sizeBytes(Built built);

    void cloneInto(Built out, Built src);
}
