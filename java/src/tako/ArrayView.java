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
import tako.FixedSizeTakoType;

public class ArrayView<
    InnerRendered, InnerBuilt, InnerTakoType extends FixedSizeTakoType<InnerRendered, InnerBuilt>> {

    private final InnerTakoType itt;
    private final ArrayList<InnerRendered> inner;

    private ByteBuffer buf;
    private int offset;


    public ArrayView(InnerTakoType itt, int size) {
        this.itt = itt;
        inner = new ArrayList<InnerRendered>();
        for (int i = 0; i < size; i ++) {
            inner.add(itt.newRendered());
        }
    }

    public void render(ByteBuffer buf, int offset) {
        this.buf = buf;
        this.offset = offset;
        for (int i = 0; i < inner.size(); i++) {
            itt.render(inner.get(i), buf, offsetOfIndex(i));
        }
    }

    public int parse(ByteBuffer buf, int offset) throws ParseException {
        this.buf = buf;
        this.offset = offset;
        for (int i = 0; i < inner.size(); i++) {
            itt.parse(inner.get(i), buf, offsetOfIndex(i));
        }
        return offsetOfIndex(inner.size());
    }

    public void build(ArrayList<InnerBuilt> out) {
        out.clear();
        for (int i = 0; i < inner.size(); i++) {
            InnerBuilt built = itt.newBuilt();
            itt.build(built, get(i));
            out.add(built);
        }
    }

    public InnerRendered get(int index) {
        return inner.get(index);
    }

    public int size() {
        return inner.size();
    }

    private int offsetOfIndex(int index) {
        return offset + index * itt.sizeBytes();
    }
}
