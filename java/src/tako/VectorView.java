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

public class VectorView<
    InnerRendered, InnerBuilt, InnerTakoType extends FixedSizeTakoType<InnerRendered, InnerBuilt>> {

    private final InnerTakoType itt;
    private final ArrayList<InnerRendered> inner;

    private ByteBuffer buf;
    private int offset;
    private int size;


    public VectorView(InnerTakoType itt) {
        this.itt = itt;
        inner = new ArrayList<InnerRendered>();
    }

    private void setup(ByteBuffer buf, int offset, int size) {
        this.buf = buf;
        this.offset = offset;
        this.size = size;
        inner.ensureCapacity(size);
        for (int i = inner.size(); i < size; i++) {
            inner.add(itt.newRendered());
        }
    }

    public void render(ByteBuffer buf, int offset, int size) {
        setup(buf, offset, size);
        for (int i = 0; i < size; i++) {
            itt.render(inner.get(i), buf, offsetOfIndex(i));
        }
    }

    public int parse(ByteBuffer buf, int offset, int size) throws ParseException {
        setup(buf, offset, size);
        for (int i = 0; i < size; i++) {
            itt.parse(inner.get(i), buf, offsetOfIndex(i));
        }
        return offsetOfIndex(size);
    }

    public void build(ArrayList<InnerBuilt> out) {
        out.clear();
        for (int i = 0; i < size; i++) {
            InnerBuilt built = itt.newBuilt();
            itt.build(built, get(i));
            out.add(built);
        }
    }

    public InnerRendered get(int index) {
        if (index >= size) {
            throw new IndexOutOfBoundsException();
        }
        return inner.get(index);
    }

    public int size() {
        return size;
    }

    private int offsetOfIndex(int index) {
        return offset + index * itt.sizeBytes();
    }
}

