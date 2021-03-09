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
import java.util.ArrayList;
import tako.SimpleTakoType;

public class ListView<
    InnerRendered, InnerBuilt, InnerTakoType extends SimpleTakoType<InnerRendered, InnerBuilt>> {

    private final InnerTakoType itt;

    private ByteBuffer buf;
    private int offset;
    private int size;
    private ArrayList<InnerRendered> parts;


    public ListView(InnerTakoType itt) {
        this.itt = itt;
        this.parts = new ArrayList<>();
    }

    public int parse(ByteBuffer buf, int offset, int size) throws ParseException {
        this.buf = buf;
        this.offset = offset;
        this.size = size;
        this.parts.ensureCapacity(size);
        // Add more elements to parts if needed.
        for (int i = parts.size(); i < size; i++) {
            this.parts.add(itt.newRendered());
        }

        for (int i = 0; i < size; i++) {
            offset = itt.parse(parts.get(i), buf, offset);
        }
        return offset;
    }

    public void build(ArrayList<InnerBuilt> out) {
        out.clear();
        for (int i = 0; i < size; i++) {
            InnerBuilt built = itt.newBuilt();
            itt.build(built, parts.get(i));
            out.add(built);
        }
    }

    public InnerRendered get(int index) {
        if (index >= size) {
            throw new IndexOutOfBoundsException();
        }
        return parts.get(index);
    }

    public int size() {
        return size;
    }
}
