""" unit tests """
import pytest

from typing import cast

from ae.base import UNSET
from ae.deep import deep_assignment, deep_object, deep_replace, deep_search


class TestHelpers:
    def test_deep_assignment_dict(self):
        tst_str = "bCd"
        tst_tup = (0, "1", 2.3)
        dic = dict(str_item=tst_str, tup_item=tst_tup)

        deep_assignment([(dic, 'str_item'), (tst_str, 0)], "_")
        assert tst_str[0] == 'b'
        assert dic['str_item'][0] == '_'

        deep_assignment([(dic, 'str_item'), ('_Cd', 0)], "B")
        assert dic['str_item'][0] == 'B'

        deep_assignment([(dic, 'str_item'), ('BCd', 2)], 'D')
        assert dic['str_item'][2] == 'D'
        assert dic['str_item'] == "BCD"
        assert deep_object(dic, 'str_item') == "BCD"

        deep_assignment([(dic, 'str_item')], tst_str)
        assert dic['str_item'] == tst_str

        assert dic['tup_item'][1] == "1"
        deep_assignment([(dic, 'tup_item'), (tst_tup, 1)], 1)
        assert dic['tup_item'][1] == 1
        assert deep_object(dic, "['tup_item'][1]") == 1

        deep_assignment([(dic, "tup_item")], "new_string")
        assert dic['tup_item'] == "new_string"
        assert deep_object(dic, "['tup_item']") == "new_string"

    def test_deep_assignment_list(self):
        tst_str = "bCd"
        tst_tup = (0, "1", 2.3)
        lst = ['a', tst_str, tst_tup]

        deep_assignment([(lst, 1), (tst_str, 0)], "_")
        assert lst[1][0] == "_"

        deep_assignment([(lst, 1), ('_Cd', 0)], "x")
        assert lst[1][0] == "x"
        deep_assignment([(lst, 1), ('xCd', 1)], "y")
        deep_assignment([(lst, 1), ('xyd', 2)], "z")
        assert lst[1] == "xyz"
        assert deep_object(lst, "[1]") == "xyz"

        deep_assignment([(lst, 2), ('xyz', 1)], "Y")
        assert lst[2][1] == "Y"
        assert deep_object(lst, "[2][1]") == "Y"

        deep_assignment([(lst, 2)], "new_string")
        assert lst[2] == "new_string"
        assert deep_object(lst, "2]") == "new_string"

    def test_deep_assignment_obj(self):
        tst_str = "bCd"
        tst_tup = (0, "1", 2.3)

        class Tst:
            """ test object """
            str_att = tst_str
            tup_att = tst_tup
        obj = Tst()
        deep_assignment([(obj, 'str_att'), (tst_str, 0)], "_")
        assert tst_str[0] == 'b'
        assert obj.str_att[0] == '_'

        deep_assignment([(obj, 'str_att'), ('_Cd', 0)], "B")
        assert obj.str_att[0] == 'B'

        deep_assignment([(obj, 'str_att'), ('BCd', 2)], 'D')
        assert obj.str_att[2] == 'D'
        assert obj.str_att == "BCD"
        assert deep_object(obj, 'str_att') == "BCD"

        deep_assignment([(obj, 'str_att')], tst_str)
        assert obj.str_att == tst_str

        assert obj.tup_att[1] == "1"
        deep_assignment([(obj, 'tup_att'), (tst_tup, 1)], 1)
        assert obj.tup_att[1] == 1
        assert deep_object(obj, "tup_att[1]") == 1

        deep_assignment([(obj, "tup_att")], "new_string")
        assert obj.tup_att == "new_string"
        assert deep_object(obj, "tup_att") == "new_string"

    def test_deep_assignment_exception(self):
        tst_str = "bCd"
        tst_tup = (0, "1", 2.3)

        with pytest.raises(ValueError):
            deep_assignment([(tst_str, 1)], "_")
        with pytest.raises(ValueError):
            deep_assignment([(tst_tup, 1)], "_")
        with pytest.raises(ValueError):
            deep_assignment([(tst_tup, 1), (tst_tup, 0)], "_")

        dic = dict(str_item=tst_str, tup_item=tst_tup)
        with pytest.raises(TypeError):
            deep_assignment([(dic, 'str_item'), (tst_str, 0)], 99)
        with pytest.raises(TypeError):
            deep_assignment([(dic, 'tup_item'), (tst_tup, 1), ("1", 2)], 1)

        lst = ['a', tst_str, tst_tup]
        with pytest.raises(TypeError):
            deep_assignment([(lst, 1), (tst_str, 0)], 33)
        with pytest.raises(TypeError):
            deep_assignment([(lst, 2), (tst_tup, 1), ("1", 0)], 33)

        class Tst:
            """ test object """
            str_att = tst_str
            tup_att = tst_tup
        obj = Tst()
        with pytest.raises(TypeError):
            deep_assignment([(obj, 'str_att'), (tst_str, 0)], 33)
        with pytest.raises(TypeError):
            deep_assignment([(obj, 'tup_att'), (tst_tup, 1), ("1", 0)], 33)

    def test_deep_object_get(self):
        class TstA:
            """ test class """
            att = 'a_att_value'
            dic = dict(a_key='a_dict_val', a_dict={'a_key': 'a_a_dict_val', 33: 'a_a_num_key_val'})
            lis = ['a_list_val']

        class TstB:
            """ test class """
            att = 'b_att_value'
            a_att = TstA()

        a = TstA()
        b = TstB()
        c = list((TstA(), b))
        d = dict(a=TstA(), b=b, c=c)

        assert deep_object(a, 'att') == 'a_att_value'
        assert deep_object(a, 'att[-1]') == 'e'
        assert deep_object(a, "dic['a_key']") == 'a_dict_val'
        assert deep_object(a, 'dic["a_key"]') == 'a_dict_val'
        assert deep_object(a, 'dic[a_key]') == 'a_dict_val'
        assert deep_object(a, "dic['a_dict']") == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(a, "dic['a_dict']['a_key']") == 'a_a_dict_val'
        assert deep_object(a, "dic['a_dict'][33]") == 'a_a_num_key_val'
        assert deep_object(a, "lis[0]") == 'a_list_val'

        assert deep_object(b, 'att') == 'b_att_value'
        assert isinstance(deep_object(b, 'a_att'), TstA)
        assert deep_object(b, 'a_att.att') == 'a_att_value'
        assert deep_object(b, 'a_att.att[-1]') == 'e'
        assert deep_object(b, "a_att.dic['a_key']") == 'a_dict_val'
        assert deep_object(b, "a_att.dic['a_dict']") == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(b, "a_att.dic['a_dict']['a_key']") == 'a_a_dict_val'
        assert deep_object(b, "a_att.dic['a_dict'][33]") == 'a_a_num_key_val'
        assert deep_object(b, "a_att.lis[0]") == 'a_list_val'

        assert deep_object(c, '[0].att') == 'a_att_value'
        assert deep_object(c, '0].att') == 'a_att_value'
        assert isinstance(deep_object(c, '0]'), TstA)
        assert deep_object(c, '0].att[-1]') == 'e'
        assert deep_object(c, "0].dic['a_key']") == 'a_dict_val'
        assert deep_object(c, "0].dic['a_dict']") == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(c, "0].dic['a_dict']['a_key']") == 'a_a_dict_val'
        assert deep_object(c, "0].dic['a_dict'][33]") == 'a_a_num_key_val'
        assert deep_object(c, "0].lis[0]") == 'a_list_val'

        assert deep_object(c, '1].a_att.att') == 'a_att_value'
        assert isinstance(deep_object(c, '1].a_att'), TstA)
        assert deep_object(c, '1].a_att.att[-1]') == 'e'
        assert deep_object(c, "1].a_att.dic['a_key']") == 'a_dict_val'
        assert deep_object(c, "1].a_att.dic['a_dict']") == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(c, "1].a_att.dic['a_dict']['a_key']") == 'a_a_dict_val'
        assert deep_object(c, "1].a_att.dic['a_dict'][33]") == 'a_a_num_key_val'
        assert deep_object(c, "1].a_att.lis[0]") == 'a_list_val'

        assert deep_object(d, "'a'].att") == 'a_att_value'
        assert isinstance(deep_object(d, "'a']"), TstA)
        assert deep_object(d, "'a'].att[-1]") == 'e'
        assert deep_object(d, "'a'].dic['a_key']") == 'a_dict_val'
        assert deep_object(d, "'a'].dic['a_dict']") == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(d, "'a'].dic['a_dict']['a_key']") == 'a_a_dict_val'
        assert deep_object(d, "'a'].dic['a_dict'][33]") == 'a_a_num_key_val'
        assert deep_object(d, "'a'].lis[0]") == 'a_list_val'

        assert deep_object(d, "a].att") == 'a_att_value'
        assert isinstance(deep_object(d, "a]"), TstA)
        assert deep_object(d, "a].att[-1]") == 'e'
        assert deep_object(d, "a].dic['a_key']") == 'a_dict_val'
        assert deep_object(d, "a].dic['a_dict']") == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(d, "a].dic['a_dict']['a_key']") == 'a_a_dict_val'
        assert deep_object(d, "a].dic['a_dict'][33]") == 'a_a_num_key_val'
        assert deep_object(d, "a].lis[0]") == 'a_list_val'

        assert deep_object(d, 'b].att') == 'b_att_value'
        assert deep_object(d, 'b].a_att.att') == 'a_att_value'
        assert deep_object(d, 'b].a_att.att[-1]') == 'e'
        assert deep_object(d, "b].a_att.dic['a_key']") == 'a_dict_val'
        assert deep_object(d, "b].a_att.dic['a_dict']") == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(d, "b].a_att.dic['a_dict']['a_key']") == 'a_a_dict_val'
        assert deep_object(d, "b].a_att.dic['a_dict'][33]") == 'a_a_num_key_val'
        assert deep_object(d, "b].a_att.lis[0]") == 'a_list_val'

        assert deep_object(d, 'c][0].att') == 'a_att_value'
        assert deep_object(d, 'c][0].att') == 'a_att_value'
        assert deep_object(d, 'c][0].att[-1]') == 'e'
        assert deep_object(d, "c][0].dic['a_key']") == 'a_dict_val'
        assert deep_object(d, "c][0].dic['a_dict']") == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(d, "c][0].dic['a_dict']['a_key']") == 'a_a_dict_val'
        assert deep_object(d, "c][0].dic['a_dict'][33]") == 'a_a_num_key_val'
        assert deep_object(d, "c][0].lis[0]") == 'a_list_val'

        assert deep_object(a, "invalid_attr") == UNSET
        assert deep_object(a, "[invalid_key]") == UNSET
        with pytest.raises(TypeError):
            deep_object(c, "[invalid_idx]")
        assert deep_object(d, "[invalid_key]") == UNSET

    def test_deep_object_set(self):
        class TstA:
            """ test class """
            att = 'a_att_value'
            dic = dict(a_key='a_dict_val', a_dict={'a_key': 'a_a_dict_val', 33: 'a_a_num_key_val'})
            lis = ['a_list_val']
            tup = (0, "1", 2.3)

        class TstB:
            """ test class """
            att = 'b_att_value'
            a_att = TstA()

        a = TstA()
        b = TstB()

        assert deep_object(a, 'att', new_value='a_att_new_value') == 'a_att_value'
        assert deep_object(a, 'att') == 'a_att_new_value'

        assert deep_object(a, "dic['a_key']", new_value='a_dict_new_val') == 'a_dict_val'
        assert deep_object(a, 'dic["a_key"]') == 'a_dict_new_val'

        assert deep_object(a, "dic[99]", new_value='new_dict_item_with_int_key') == UNSET
        assert deep_object(a, "dic[99]") == 'new_dict_item_with_int_key'

        assert deep_object(a, "dic['a_dict']", {'a_key': 'a_a_dict_new_val', 33: 'a_a_num_key_val'}
                           ) == {33: 'a_a_num_key_val', 'a_key': 'a_a_dict_val'}
        assert deep_object(a, "dic['a_dict']['a_key']", new_value='a_a_dict_newer_val') == 'a_a_dict_new_val'
        assert deep_object(a, "dic['a_dict']['a_key']") == 'a_a_dict_newer_val'
        assert deep_object(b, "a_att.dic['a_dict']['a_key']") == 'a_a_dict_newer_val'

        assert deep_object(a, "dic['a_dict'][33]", new_value='new_dict_with_int_key') == 'a_a_num_key_val'
        assert deep_object(a, "dic['a_dict'][33]") == 'new_dict_with_int_key'

        assert deep_object(a, "lis[0]", new_value='a_list_new_val') == 'a_list_val'
        assert deep_object(a, "lis[0]") == 'a_list_new_val'
        assert deep_object(b, "a_att.lis[0]") == 'a_list_new_val'

        assert deep_object(b, 'att', new_value='b_att_new_value') == 'b_att_value'
        assert deep_object(b, 'att') == 'b_att_new_value'

        assert deep_object(b, 'a_att.att', new_value='xxx') == 'a_att_value'
        assert deep_object(b, 'a_att.att') == 'xxx'
        assert deep_object(b, 'a_att.att[-1]') == 'x'

    def test_deep_object_set_immutable(self):
        tst_str = "bCd"
        tst_tup = (0, "1", 2.3)

        class Tst:
            """ test class """
            dic_att = dict(str_item=tst_str, tup_item=tst_tup)

        dic = dict(str_item=tst_str, tup_item=tst_tup)
        obj = Tst()

        assert deep_object(dic, "str_item[0]", new_value="B") == 'b'
        assert deep_object(dic, "str_item[0]") == 'B'
        assert deep_object(dic, "str_item", new_value=tst_str) == 'BCd'
        assert dic['str_item'] == tst_str

        assert deep_object(obj, "dic_att[str_item][2]") == 'd'
        assert deep_object(obj, "dic_att['str_item'][2]", new_value='D') == "d"
        assert obj.dic_att['str_item'][2] == "D"

        assert deep_object(dic, "tup_item[1]", new_value=1) == "1"
        assert dic['tup_item'][1] == 1
        assert deep_object(dic, "tup_item][1]") == 1

    def test_deep_object_dict_keys(self):
        d = dict()

        assert 123 not in d
        assert deep_object(d, '[123]', new_value="int_key_val") == UNSET
        assert deep_object(d, '[123]') == "int_key_val"
        assert 123 in d

        assert "123" not in d
        assert deep_object(d, '["123"]', new_value="str_key_val") == UNSET
        assert deep_object(d, '["123"]') == "str_key_val"
        assert "123" in d

        assert (1, "2") not in d
        assert deep_object(d, '[(1, "2")]', new_value="tuple_key_val") == UNSET
        assert deep_object(d, '[(1, "2")]') == "tuple_key_val"
        assert (1, "2") in d

    def test_deep_replace_data(self):
        sub = ['b_list_0', 'search_index_value', 'search_key_value3']
        data = dict(
            a_str='a_str',
            a_list=['a_list_0', 'search_index_value', 2, dict(
                a_list_a='a_list_a_str', search_key='search_key_value1')],
            a_dict=dict(
                b_str="b_str",
                b_dict=dict(
                    c_tuple=('1st_tuple_value', 'search_value', '3rd_tuple_value', 3, ),
                    c_str='c str',
                    search_key='search_key_value2',
                ),
                b_list=sub,
            )
        )

        deep_replace(data, lambda p, k, v: 'replaced_value' if v == 'search_value' else UNSET)
        assert data['a_dict']['b_dict']['c_tuple'][1] == 'replaced_value'

        deep_replace(data, lambda p, k, v: 'replaced_index_value' if k == 2 else UNSET)     # search_index_value
        assert data['a_list'][2] == 'replaced_index_value'
        assert data['a_dict']['b_list'][2] == 'replaced_index_value'

        obj_path = [(data, 'a_dict'), (data['a_dict'], 'b_list'), (data['a_dict']['b_list'], 2)]
        deep_replace(data, lambda p, k, v: 'replaced_key_value' if k == 'search_key' or p == obj_path else UNSET)
        assert data['a_list'][3]['search_key'] == 'replaced_key_value'
        assert data['a_dict']['b_dict']['search_key'] == 'replaced_key_value'
        assert data['a_dict']['b_list'][2] == 'replaced_key_value'

        deep_replace(data, lambda p, k, v: 'WIPED')
        for _k, _v in data.items():
            assert _v == 'WIPED'

    def test_deep_replace_exception(self):
        with pytest.raises(ValueError):
            deep_replace(cast(list, ('tuple', 'are', 'only', 'replace', 'in', 'deeper', 'data')),
                         lambda d, k, v: 'replacing all')

    def test_deep_replace_immutable(self):
        tst_str = "AbCbE"
        tst_tuple = (3, '0', 1)
        tst_list = [tst_str, tst_tuple]
        tst_dict = dict(l=tst_list)

        deep_replace(tst_dict, lambda _p, k, v: 'd' if v == 'b' and k == 3 else UNSET)
        assert tst_list[0][3] == 'b'
        deep_replace(tst_dict, lambda _p, k, v: 'd' if v == 'b' and k == 3 else UNSET, immutable_types=(str,))
        assert tst_list[0][3] == 'd'

        deep_replace(tst_dict, lambda _p, k, v: 2 if v == '0' else UNSET, immutable_types=(str,))
        assert tst_list[1][1] == '0'
        deep_replace(tst_dict, lambda _p, k, v: 2 if v == '0' else UNSET)
        assert tst_list[1][1] == 2

    def test_deep_search_dict(self):
        tst_str = "bCd"
        tst_tup = (0, tst_str, 2.3)
        dic = dict(str_item=tst_str, tup_item=tst_tup)

        obj_key = [(dic, 'str_item')]
        assert deep_search(dic, lambda p, k, v: p == obj_key) == \
               [(obj_key, 'str_item', tst_str)]

        assert deep_search(dic, lambda p, k, v: k == 2) == \
               [([(dic, 'tup_item'), (dic['tup_item'], 2)], 2, 2.3)]

        assert deep_search(dic, lambda p, k, v: v == tst_str) == \
               [([(dic, 'str_item')], 'str_item', tst_str),
                ([(dic, 'tup_item'), (dic['tup_item'], 1)], 1, tst_str),
                ]

        obj_key = [(dic, 'str_item'), (dic['str_item'], 1)]
        assert deep_search(dic, lambda p, k, v: p == obj_key) == []  # by default single chars/bytes cannot be searched

        assert deep_search(dic, lambda p, k, v: p == obj_key, skip_types=(bytes, int, float, type)) == \
               [([(dic, 'str_item'), ('bCd', 1)], 1, 'C')]

    def test_deep_search_obj(self):
        tst_str = "bCd"
        tst_tup = (0, tst_str, 2.3)

        class Tst:
            """ test class """
            dic_att = dict(str_item=tst_str, tup_item=tst_tup)

        obj = Tst()

        assert deep_search(obj, lambda p, k, v: p == [(obj, 'dic_att'), (obj.dic_att, 'str_item')]) == \
               [([(obj, 'dic_att'), (obj.dic_att, 'str_item')], 'str_item', tst_str)]

        assert deep_search(obj, lambda p, k, v: k == 2) == \
               [([(obj, 'dic_att'), (obj.dic_att, 'tup_item'), (obj.dic_att['tup_item'], 2)], 2, 2.3)]

        assert deep_search(obj, lambda p, k, v: v == tst_str) == \
               [([(obj, 'dic_att'), (obj.dic_att, 'str_item')], 'str_item', tst_str),
                ([(obj, 'dic_att'), (obj.dic_att, 'tup_item'), (obj.dic_att['tup_item'], 1)], 1, tst_str),
                ]
