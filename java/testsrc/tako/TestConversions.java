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
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import tako.ParseException;
import takogen.test_types.Conversions.FlavorOld;
import takogen.test_types.Conversions.FlavorNew;
import takogen.test_types.Conversions.CupcakeOrderOld;
import takogen.test_types.Conversions.CupcakeOrderNew;
import takogen.test_types.Conversions.CakeOrderOld;
import takogen.test_types.Conversions.CakeOrderNew;
import takogen.test_types.Conversions.CakeOrderOldView;
import takogen.test_types.Conversions.CakeOrderNewView;
import takogen.test_types.Conversions.OrderOld;
import takogen.test_types.Conversions.OrderNew;
import takogen.test_types.Conversions.MsgOld;
import takogen.test_types.Conversions.MsgNew;
import static takogen.test_types.Conversions.convert;
import static tako.Helpers.*;

public class TestConversions {
    @Test
    public void flavorOldToFlavorNew() {
        var old = FlavorOld.CHOCOLATE;
        var new_ = FlavorNew.makeUninitialized();
        convert(new_, old);
        Assertions.assertEquals(new_, FlavorNew.CHOCOLATE);
    }
    @Test
    public void flavorNewToFlavorOld() {
        var new_ = FlavorNew.CARMEL;
        var old = FlavorOld.makeUninitialized();
        convert(old, new_);
        Assertions.assertEquals(old, FlavorOld.CHOCOLATE);
    }
    @Test
    public void cupcakeOrderOldToCupcakeOrderNew() {
        var old = new CupcakeOrderOld().init()
            .flavor(FlavorOld.CHOCOLATE)
            .finish();
        var new_ = new CupcakeOrderNew();
        convert(new_, old);
        var expected = new CupcakeOrderNew().init()
            .flavor(FlavorNew.CHOCOLATE)
            .quantity(50)
            .finish();
        Assertions.assertEquals(new_, expected);
    }
    @Test
    public void cupcakeOrderNewToCupcakeOrderOld() {
        var new_ = new CupcakeOrderNew().init()
            .flavor(FlavorNew.CARMEL)
            .quantity(50)
            .finish();
        var old = new CupcakeOrderOld();
        convert(old, new_);
        var expected = new CupcakeOrderOld().init()
            .flavor(FlavorOld.CHOCOLATE)
            .finish();
        Assertions.assertEquals(old, expected);
    }
    @Test
    public void orderOldToOrderNew() {
        var old = new OrderOld();
        old.set(CupcakeOrderOld.class).init()
            .flavor(FlavorOld.CHOCOLATE)
            .finish();
        var new_ = new OrderNew();
        convert(new_, old);
        var expected = new OrderNew();
        expected.set(CupcakeOrderNew.class).init()
            .flavor(FlavorNew.CHOCOLATE)
            .quantity(50)
            .finish();
        Assertions.assertEquals(new_, expected);
    }
    @Test
    public void orderNewToOrderOld() {
        var new_ = new OrderNew();
        new_.set(CupcakeOrderNew.class).init()
            .flavor(FlavorNew.CARMEL)
            .quantity(50)
            .finish();
        var old = new OrderOld();
        convert(old, new_);
        var expected = new OrderOld();
        expected.set(CupcakeOrderOld.class).init()
            .flavor(FlavorOld.CHOCOLATE)
            .finish();
        Assertions.assertEquals(old, expected);
    }
    @Test
    public void msgOldToMsgNew() {
        var old = new MsgOld();
        old.msg().set(CupcakeOrderOld.class).init()
            .flavor(FlavorOld.CHOCOLATE);
        var new_ = new MsgNew();
        convert(new_, old);
        var expected = new MsgNew();
        expected.msg().set(CupcakeOrderNew.class).init()
            .flavor(FlavorNew.CHOCOLATE)
            .quantity(50);
        Assertions.assertEquals(new_, expected);
    }
    @Test
    public void msgNewToMsgOld() {
        var new_ = new MsgNew();
        new_.msg().set(CupcakeOrderNew.class).init()
            .flavor(FlavorNew.CARMEL)
            .quantity(50);
        var old = new MsgOld();
        convert(old, new_);
        var expected = new MsgOld();
        expected.msg().set(CupcakeOrderOld.class).init()
            .flavor(FlavorOld.CHOCOLATE);
        Assertions.assertEquals(old, expected);
    }
    @Test
    public void viewCakeOrderOldToCakeOrderNew() throws ParseException {
        var old = new CakeOrderOld().init()
            .flavor(FlavorOld.CHOCOLATE)
            .finish();
        var oldBytes = old.serialize();
        var oldView = new CakeOrderOldView();
        oldView.parse(oldBytes, 0);
        var newView = new CakeOrderNewView();
        convert(newView, oldView);
        var new_ = new CakeOrderNew().init()
            .flavor(FlavorNew.CHOCOLATE)
            .finish();
        var newViewBuilt = new CakeOrderNew();
        newView.build(newViewBuilt);
        Assertions.assertEquals(newViewBuilt, new_);
    }
}
