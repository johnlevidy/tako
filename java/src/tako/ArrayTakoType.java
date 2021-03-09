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

public class ArrayTakoType<
    InnerRendered, InnerBuilt, InnerTakoType extends FixedSizeTakoType<InnerRendered, InnerBuilt>>
    implements FixedSizeTakoType<ArrayView<InnerRendered, InnerBuilt, InnerTakoType>, ArrayList<InnerBuilt>> {

    private final InnerTakoType itt;
    private final int size;

    public ArrayTakoType(InnerTakoType itt, int size) {
        this.itt = itt;
        this.size = size;
    }

    public ArrayView<InnerRendered, InnerBuilt, InnerTakoType> newRendered() {
        return new ArrayView<InnerRendered, InnerBuilt, InnerTakoType>(itt, size);
    }
    public ArrayList<InnerBuilt> newBuilt() {
        ArrayList<InnerBuilt> result = new ArrayList<InnerBuilt>();
        for (int i = 0; i < size; i++) {
            result.add(itt.newBuilt());
        }
        return result;
    }

    public void render(ArrayView<InnerRendered, InnerBuilt, InnerTakoType> out, ByteBuffer buf, int offset) {
        out.render(buf, offset);
    }

    public int parse(ArrayView<InnerRendered, InnerBuilt, InnerTakoType> out, ByteBuffer buf, int offset) throws ParseException {
        return out.parse(buf, offset);
    }

    public void build(ArrayList<InnerBuilt> out, ArrayView<InnerRendered, InnerBuilt, InnerTakoType> rendered) {
        rendered.build(out);
    }

    public int serializeInto(ArrayList<InnerBuilt> built, ByteBuffer buf, int offset) {
        if (built.size() != size) {
            throw new WrongArraySizeException();
        }
        for (int i = 0; i < built.size(); i++) {
            offset = itt.serializeInto(built.get(i), buf, offset);
        }
        return offset;
    }

    public int sizeBytes(ArrayList<InnerBuilt> built) {
        return sizeBytes();
    }

    public int sizeBytes() {
        return size * itt.sizeBytes();
    }

    public void cloneInto(ArrayList<InnerBuilt> out, ArrayList<InnerBuilt> src) {
        for (int i = 0; i < size; i++) {
            itt.cloneInto(out.get(i), src.get(i));
        }
    }
}

