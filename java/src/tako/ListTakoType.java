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

public class ListTakoType<
    InnerRendered, InnerBuilt, InnerTakoType extends SimpleTakoType<InnerRendered, InnerBuilt>>
    implements TakoType<ListView<InnerRendered, InnerBuilt, InnerTakoType>, ArrayList<InnerBuilt>> {

    private final InnerTakoType itt;

    public ListTakoType(InnerTakoType itt) {
        this.itt = itt;
    }

    public ListView<InnerRendered, InnerBuilt, InnerTakoType> newRendered() {
        return new ListView<InnerRendered, InnerBuilt, InnerTakoType>(itt);
    }
    public ArrayList<InnerBuilt> newBuilt() {
        return new ArrayList<InnerBuilt>();
    }

    public void render(ListView<InnerRendered, InnerBuilt, InnerTakoType> out, ByteBuffer buf, int offset, int size) {
        try {
            parse(out, buf, offset, size);
        } catch (ParseException e) {
            throw new RuntimeException(e);
        }
    }

    public int parse(ListView<InnerRendered, InnerBuilt, InnerTakoType> out, ByteBuffer buf, int offset, int size) throws ParseException {
        return out.parse(buf, offset, size);
    }

    public void build(ArrayList<InnerBuilt> out, ListView<InnerRendered, InnerBuilt, InnerTakoType> rendered) {
        rendered.build(out);
    }

    public int serializeInto(ArrayList<InnerBuilt> built, ByteBuffer buf, int offset) {
        for (int i = 0; i < built.size(); i++) {
            offset = itt.serializeInto(built.get(i), buf, offset);
        }
        return offset;
    }

    public int sizeBytes(ArrayList<InnerBuilt> built) {
        int result = 0;
        for (int i = 0; i < built.size(); i++) {
            result += itt.sizeBytes(built.get(i));
        }
        return result;
    }
    public void cloneInto(ArrayList<InnerBuilt> out, ArrayList<InnerBuilt> src) {
        out.ensureCapacity(src.size());
        for (int i = src.size(); i < out.size(); i++) {
            out.add(itt.newBuilt());
        }
        while (out.size() > src.size()) {
            out.remove(out.size() - 1);
        }
        for (int i = 0; i < src.size(); i++) {
            itt.cloneInto(out.get(i), src.get(i));
        }
    }
}
