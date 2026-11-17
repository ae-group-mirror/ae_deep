"""
deeply nested data structures api
=================================

this namespace portion is pure python, depends only on the Python Standard Library and the :mod:`ae.base` portion.
see section :ref:`deeply nested data structure helpers` for examples and more info.
"""
import ast

from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence
from operator import getitem
from types import ModuleType
from typing import Any, cast

from ae.base import UNSET                                                           # type: ignore


__version__ = '0.4.15'


DataLeafTypesType = tuple[type, ...]                        #: list/tuple of types of deep data leaves
KeyType = str | int | tuple                                 #: index/attribute types of deep data structures
KeyFilterCallable = Callable[[KeyType], bool]               #: callable to filter item key/index and attribute names
ObjKeysType = list[tuple[Any, Any]]                         #: object key list of tuples of: object, key/index/attribute
ObjCheckCallable = Callable[[ObjKeysType, Any, Any], Any]   #: :func:`deep_replace`/:func:`deep_search` parameter type
ValueFilterCallable = Callable[[Any, ObjKeysType], bool]


DEFAULT_LEAF_TYPES: DataLeafTypesType = (bytes, int, float, set, str, type)  #: leaf types of deep data structures
KEY_PATH_SEPARATORS = frozenset(('.', '[', ']'))  #: separator characters in key path string
MUTABLE_DATA_TYPES = (MutableMapping, MutableSequence)      #: deep data structure node types


def deepest_key_filter(index_or_attr: KeyType) -> bool:
    """ deep reaching key filter callable, returning `True` to filter out key/index/attribute id/name.

    :param index_or_attr:       index, attribute or key in an object, list, dict or any other container/data structure.
    :return:                    `True` if the index or attribute get skipped/filtered on deep search/replace.
    """
    return (str(index_or_attr) in
            ('canvas', 'canvas_viewport', 'global_variables', 'keyboard', 'opener', 'parent', 'proxy_ref',
             'root', 'root_window', 'self', 'texture', 'window')
            )


def deepest_value_filter(value: Any, obj_keys: ObjKeysType) -> bool:
    """ deep reaching item value filter callable, returning `True` to filter out values to be scanned deeper.

    :param value:               value to check for to be filtered out.
    :param obj_keys:            list of tuples of object and attribute-or-key-in-the-object, to filter out a value
                                identical to one of the objects in this argument.
    :return:                    `True` if the specified value is either a base type (like float, int, str, and Callable)
                                or is one of the objects specified in the :paramref:`.obj_keys`
                                argument, else `False`.
    """
    return (
        not value
        or isinstance(value, (float, int, str, type(None), Callable, ModuleType))  # type: ignore # Callable ok Py>=3.8
        or any(obj is value for obj, _key_or_attr in obj_keys)
    )


def flattest_key_filter(index_or_attr: KeyType) -> bool:
    """ key filter callable, returning `True` to filter out key/index/attribute id/name.

    :param index_or_attr:       index, attribute or key in an object, list, dict or any other container/data structure.
    :return:                    `True` if the index or attribute get skipped/filtered on deep search/replace.
    """
    str_key = str(index_or_attr)
    return (str_key in ('canvas', 'canvas_viewport', 'connection', 'global_variables', 'keyboard', 'opener', 'parent',
                        'proxy_ref', 'root', 'root_window', 'self', 'texture', 'window')  # tap_widget
            or str_key.startswith('_')
            or str_key.endswith('_app')     # main_app, framework_app, fw_app
            )


def flattest_value_filter(value: Any, obj_keys: ObjKeysType) -> bool:
    """ default item value filter callable, returning `True` to filter out values to be scanned deeper.

    :param value:               value to check for to be filtered out.
    :param obj_keys:            list of tuples of object and attribute-or-key-in-the-object, to filter out a value
                                identical to one of the objects in this argument.
    :return:                    `True` if the specified value is either a base type (like float, int, str, and Callable)
                                or is one of the objects specified in the :paramref:`.obj_keys`
                                argument, else `False`.
    """
    return (
        not value
        or not isinstance(value, (dict, list, tuple))
        or any(obj is value for obj, _key_or_attr in obj_keys)
    )


def deep_replace(obj: Any,  # pylint: disable=too-many-arguments,too-many-positional-arguments
                 replace_with: ObjCheckCallable,
                 leaf_types: DataLeafTypesType = DEFAULT_LEAF_TYPES,
                 key_filter: KeyFilterCallable = flattest_key_filter,
                 value_filter: ValueFilterCallable = flattest_value_filter,
                 obj_keys: ObjKeysType | None = None) -> int:
    """ replace values (bottom up) within the passed (deeply nested) data structure.

    :param obj:                 mutable sequence or mapping data structure to be deep searched and replaced. can contain
                                any combination of deep nested data objects. mutable node objects (e.g. dict/list)
                                as well as the immutable types not included in :paramref:`.leaf_types`
                                will be recursively deep searched (top down) by passing their items one by one
                                to the callback function specified by :paramref:`.replace_with`.
    :param replace_with:        called for each item with the 3 arguments object key list, key in parent data-structure,
                                and the object/value. any return value other than :data:`~ae.base.UNSET` will be used to
                                overwrite the node/leaf object in the data-structure.
    :param leaf_types:          tuple of leaf types to skip from to be searched deeper. the default value of this
                                parameter is specified in the modul constant :data:`DEFAULT_LEAF_TYPES`.
    :param key_filter:          called for each sub-item/-attribute of the data structure specified by the argument
                                :paramref:`.obj`.
                                return `True` for item-key/item-index/attribute-name to be filtered out. by default all
                                attribute/key names starting with an underscore character will be filtered out
                                (see default callable :func:`flattest_key_filter`).
    :param value_filter:        called for each sub-item/-attribute of the data structure specified by
                                :paramref:`.obj` argument.
                                return `True` for items/attributes values to be filtered out. by default empty and
                                empty values, and already scanned objects will be filtered out (see default callable
                                :func:`flattest_value_filter`).
    :param obj_keys:            used (internally only) to pass the parent data-struct path in recursive calls.
    :return:                    the number of levels of the first mutable data objects above the changed data object,
                                or 0 of the changed data object is mutable.
    :raises:                    `ValueError` if no mutable parent object is in the data structure (specified in the
                                :paramref:`.obj` argument).
    :raises:                    `AttributeError` e.g. if :paramref:`.obj` is of type int, and `int` is
                                missing in the :paramref:`.leaf_types` argument.
    """
    if obj_keys is None:
        obj_keys = []

    mutable_offset = 0
    for key, value in object_items(obj, leaf_types=leaf_types, key_filter=key_filter):
        if mutable_offset:
            obj = key_list_object(obj_keys[-mutable_offset:])
        obj_keys.append((obj, key))
        new_value = replace_with(obj_keys, key, value)
        if new_value is not UNSET:
            mutable_offset = replace_object(obj_keys, new_value)
        elif not value_filter(value, obj_keys):
            mutable_offset = deep_replace(value, replace_with,
                                          leaf_types=leaf_types, key_filter=key_filter, value_filter=value_filter,
                                          obj_keys=obj_keys)
        obj_keys.pop()

    return max(mutable_offset - 1, 0)


def deep_search(obj: Any, found: ObjCheckCallable,  # pylint: disable=too-many-arguments,too-many-positional-arguments
                leaf_types: DataLeafTypesType = DEFAULT_LEAF_TYPES,
                key_filter: KeyFilterCallable = flattest_key_filter,
                value_filter: ValueFilterCallable = flattest_value_filter,
                obj_keys: ObjKeysType | None = None
                ) -> list[tuple[ObjKeysType, Any, Any]]:
    """ search key and/or value within the passed (deeply nested) data object structure.

    :param obj:                 root object to start the top-down deep search from, which can contain any combination of
                                deep nested elements/objects. for each sub-element the callable passed into
                                :paramref:`.found` will be executed. if the callable returns `True` then
                                the data path, the key and the value will be stored in a tuple and added to the search
                                result list (finally returned to the caller of this function).
                                for iterable objects of type dict/tuple/list, the sub-items will be searched, as well as
                                the attributes determined via the Python :func:`dir` function. to reduce the number of
                                items/attributes to be searched use the parameters :paramref:`.leaf_types`
                                and/or :paramref:`.key_filter`.
    :param found:               called for each item with 3 arguments (data-struct-path, key in data-structure, value),
                                and if the return value is `True` then the data/object path, the last key and value
                                will be added as a new item to the returned list.
    :param leaf_types:          tuple of leaf types to skip from to be searched deeper. the default value of this
                                parameter is specified in the modul constant :data:`DEFAULT_LEAF_TYPES`.
    :param key_filter:          called for each sub-item/-attribute of the data structure specified by :paramref:`.obj`.
                                return `True` for item-key/item-index/attribute-name to be filtered out. by default all
                                attribute/key names starting with an underscore character will be filtered out
                                (see default callable :func:`deepest_key_filter`).
    :param value_filter:        called for each sub-item/-attribute of the data structure specified by :paramref:`.obj`
                                argument. return `True` for items/attributes values to be filtered out. by default empty
                                and empty values, and already scanned objects will be filtered out (see default callable
                                :func:`flattest_value_filter`).
    :param obj_keys:            used (internally only) to pass the parent data-struct path in recursive calls.
    :return:                    list of tuples (data-struct-path, key, value); one tuple for each found item within the
                                passed :paramref:`.obj` argument. an empty list will be returned if
                                no item got found.
    """
    if obj_keys is None:
        obj_keys = []

    ret = []
    for key, value in object_items(obj, leaf_types=leaf_types, key_filter=key_filter):
        obj_keys.append((obj, key))
        if found(obj_keys, key, value):
            ret.append((obj_keys.copy(), key, value))
        if not value_filter(value, obj_keys):
            ret.extend(deep_search(value, found,
                                   leaf_types=leaf_types, key_filter=key_filter, value_filter=value_filter,
                                   obj_keys=obj_keys))
        obj_keys.pop()

    return ret


def deep_update(obj: Any,                   # pylint: disable=too-many-arguments,too-many-positional-arguments
                updating_obj: Any,
                leaf_types: DataLeafTypesType = DEFAULT_LEAF_TYPES,
                key_filter: KeyFilterCallable = flattest_key_filter,
                value_filter: ValueFilterCallable = flattest_value_filter,
                obj_keys: ObjKeysType | None = None
                ):
    """ merge the :paramref:`.updating_obj` data structure into the similar structured node object :paramref:`.obj`.

    :param obj:                 deep data object to update.
    :param updating_obj:        data structure similar structured like the :paramref:`.obj` argument with update values.
                                a :data:`~ae.base.UNSET` value will delete the item from the :paramref:`.obj` argument.
    :param leaf_types:          tuple of leaf types to skip from to be searched deeper. the default value of this
                                parameter is specified in the modul constant :data:`DEFAULT_LEAF_TYPES`.
    :param key_filter:          called for each sub-item/-attribute of the data structure specified by :paramref:`.obj`.
                                return `True` for item-key/item-index/attribute-name to be filtered out. by default all
                                attribute/key names starting with an underscore character will be filtered out
                                (see default callable :func:`flattest_key_filter`).
    :param value_filter:        called for each sub-item/-attribute of the data structure specified by
                                :paramref:`.obj` argument.
                                return `True` for items/attributes values to be filtered out. by default empty and
                                empty values, and already scanned objects will be filtered out (see default callable
                                :func:`flattest_value_filter`).
    :param obj_keys:            used (internally only) to pass the parent data-struct path in recursive calls.
    """
    if obj_keys is None:
        obj_keys = []

    for key, value in reversed(object_items(updating_obj, leaf_types=leaf_types, key_filter=key_filter)):
        if value is UNSET:
            pop_object([(obj, key)])
            continue

        obj_keys.append((obj, key))
        obj_val = object_item_value(obj, key)
        if obj_val is UNSET or isinstance(obj_val, leaf_types):
            replace_object([(obj, key)], value)
        elif not value_filter(value, obj_keys):
            deep_update(obj_val, value,
                        leaf_types=leaf_types, key_filter=key_filter, value_filter=value_filter,
                        obj_keys=obj_keys)
        obj_keys.pop()


def key_list_object(obj_keys: ObjKeysType) -> Any:
    """ determine object in a deep nested data structure via an object key list.

    :param obj_keys:            object key list.
    :return:                    recalculated object referenced by the first object and the keys of :paramref:`.obj_keys`
                                or `~ae.base.UNSET` if not found.
    :raises:                    TypeError if key does not match the object type in any item of :paramref:`.obj_keys`.
                                ValueError if :paramref:`.obj_keys` is not of type :data:`ObjKeysType`.
    """
    if not obj_keys:
        return UNSET

    obj = obj_keys[0][0]
    for _, key in obj_keys:
        obj = object_item_value(obj, key)

    return obj


def key_path_object(obj: Any, key_path: str, new_value: Any | None = UNSET) -> Any:
    """ determine object in a deep nested data structure via a key path string, and optionally assign a new value to it.

        :param obj:             initial data object to search in (and its sub-objects).
        :param key_path:        composed key string containing dict keys, tuple/list/str indexes and object attribute
                                names, separated by a dot character. see examples in the section
                                :ref:`referencing a deep data object`.
        :param new_value:       optional new sub object value which will replace the found object.
                                the old object value will be returned.
        :return:                value of the object specified via :paramref:`.key_path` (the old object value if
                                the argument :paramref:`.new_value` got specified)
                                or :data:`~ae.base.UNSET` if not found/exists (:paramref:`.key_path` is invalid).
        """
    if key_path[0] == '[':
        key_path = key_path[1:]       # to support fully specified indexes (starting with a square bracket)

    obj_keys = []
    while key_path and obj is not UNSET:
        key, sep, key_path = next_key_of_path(key_path)

        next_sep = ''
        next_path = key_path
        while True:
            next_obj = object_item_value(obj, key)
            if next_obj is UNSET and next_sep == ']':
                next_obj = object_item_value(obj, key + next_sep)
            if next_obj is not UNSET:
                key_path = next_path
                break
            if not next_path:
                break
            next_key, next_sep, next_path = next_key_of_path(next_path)  # search for str key with separator (.[])
            key += sep + str(next_key)
            sep = next_sep

        obj_keys.append((obj, key))
        obj = next_obj

    if new_value is not UNSET and obj_keys:
        replace_object(obj_keys, new_value)

    return obj


def key_path_string(obj_keys: ObjKeysType) -> str:
    """ convert obj keys path into deep object key path string.

    :param obj_keys:            object key list to convert.
    :return:                    key path string of the object keys path specified by the :paramref:`.obj_keys` argument.
    """
    key_path = ''
    for _obj, key in obj_keys:
        key_path += '.' + str(key)  # repr(key) not needed because high commas can be omitted from string keys
    return key_path[1:]


def key_value(key_str: str) -> Any:
    """ convert key string (mapping key, sequence index, obj attribute) into its value (str, int, float, tuple, ..). """
    try:
        key = ast.literal_eval(key_str)
    except (SyntaxError, ValueError):
        key = key_str
    return key


def next_key_of_path(key_path: str) -> tuple[Any, str, str]:
    """ parse key_path to determine the next item key/index, the path separator and the rest of the key path.

    :param key_path:            data object key/index path string to parse.
    :return:                    tuple of key/index, the separator character and the (unparsed) rest of the
                                key path (possibly an empty string).
    :raises:                    IndexError if the argument of :paramref:`.key_path` is an empty string.
    """
    idx = 0
    char = key_path[0]
    if char in ('"', "'"):
        idx += 1
    for char in key_path[idx:]:
        if char in KEY_PATH_SEPARATORS:  # ~== char in '.[]' - keep string characters separate in tuple for speedup
            break
        idx += 1

    key = key_value(key_path[:idx])

    if char == ']':
        idx += 1

    return key, char if char in KEY_PATH_SEPARATORS else '', key_path[idx + 1:]


def object_items(obj: Any,
                 leaf_types: DataLeafTypesType = DEFAULT_LEAF_TYPES,
                 key_filter: KeyFilterCallable = flattest_key_filter
                 ) -> ObjKeysType:
    """ determine the items of a data object, with mapping keys, sequence indexes or attribute names and its values.

    :param obj:                 data structure/node object (list, dict, set, tuple, data object).
    :param leaf_types:          tuple of leaf types to skip from to be searched deeper. the default value of this
                                parameter is specified in the modul constant :data:`DEFAULT_LEAF_TYPES`.
    :param key_filter:          called for each sub-item/-attribute of the data structure specified by :paramref:`.obj`.
                                return `True` for item-key/item-index/attribute-name to be filtered out. by default all
                                attribute/key names starting with an underscore character will be filtered out
                                (see default callable :func:`flattest_key_filter`).
    :return:                    items view of the data object specified in the :paramref:`.obj` argument.
    """
    if isinstance(obj, leaf_types):
        return []

    if isinstance(obj, Mapping):
        # noinspection PyInvalidCast
        items = cast(ObjKeysType, obj.items())
    elif isinstance(obj, (Sequence, set, str)):
        items = enumerate(obj)                              # type: ignore # treat tuple/lists/set index as dict key
    else:
        items = []
        for key in dir(obj):                                # treat object attribute name as dict key
            try:
                items.append((key, getattr(obj, key)))
            except (AttributeError, IndexError, Exception):         # pylint: disable=broad-except
                # ignore read-only attributes (e.g. kivy.graphics.vertex_instructions.Line.bezier)
                # and generator-index (kivy.graphics.context_instructions.PopMatrix.stack.__get__)
                pass

    return [(key, value) for key, value in items if not key_filter(key)]


def object_item_value(obj: Any, key: Any, default_value: Any = UNSET) -> Any:
    """ determine value of a data object item/attribute.

    :param obj:                 data structure object to get item/attribute value from.
    :param key:                 mapping key, attribute name or sequence index of the item/attribute.
    :param default_value:       default value to return if the item/attribute does not exist in :paramref:`.obj`.
    :return:                    data object item/attribute value
                                or the :paramref:`.default_value` argument value if not found.
    """
    get_func = getitem if isinstance(obj, (Mapping, Sequence, str)) else getattr
    try:
        return get_func(obj, key)
    except (AttributeError, IndexError, KeyError, ValueError):
        return default_value


def pop_object(obj_keys: ObjKeysType) -> list[Any]:
    """ delete sub-attribute/item of a data object.

    :param obj_keys:            list of (object, key) tuples identifying an element within a deeply nested data
                                structure or object hierarchy. the root of the data/object structure is the object at
                                list index 0 and the element to be deleted is identified by the object and key in the
                                last list item of this argument.
                                the referenced data structure can contain even immutable node objects (like tuples)
                                which will be accordingly changed/replaced if affected/needed. for that
                                at least one object/element above the immutable object in the deep data structure has
                                to be mutable, else a :class:`ValueError` will be raised.
    :return:                    list of deleted values or :data:`~ae.base.UNSET` if not found.
    :raises:                    ValueError if no immutable parent object got found or if the :paramref:`.obj_keys'
                                is empty.
                                IndexError if the one of the specified indexes in :paramref:`.obj_keys` does not exist.
    """
    new_value = pop_value = UNSET
    for obj, key_or_attr in reversed(obj_keys):
        if isinstance(obj, MUTABLE_DATA_TYPES):
            if pop_value is UNSET:
                pop_value = obj.pop(key_or_attr)
            else:
                obj[key_or_attr] = new_value

        elif isinstance(obj, Sequence):     # tuple, str or any immutable sequence type that supports the + operator
            if pop_value is UNSET:
                pop_value = obj[key_or_attr]
                new_value = obj[:key_or_attr] + obj[key_or_attr + 1:]  # type: ignore
            else:
                if isinstance(obj, tuple):
                    new_value = (new_value, )
                # noinspection unsupported-operator
                new_value = obj[:key_or_attr] + new_value + obj[key_or_attr + 1:]
            continue

        else:
            if pop_value is UNSET:
                pop_value = getattr(obj, key_or_attr)
                delattr(obj.__class__, key_or_attr)
            else:
                setattr(obj, key_or_attr, new_value)

        return pop_value

    raise ValueError(f"pop_object() error: no mutable object found in {obj_keys}")


def replace_object(obj_keys: ObjKeysType, new_value: Any) -> int:
    """ set sub-attribute/item with a mutable parent object to a new value within a deeply nested object/data structure.

    :param obj_keys:            list of (object, key) tuples identifying an element within a deeply nested data
                                structure or object hierarchy. the root of the data/object structure is the object at
                                list index 0 and the element to be changed is identified by the object and key in the
                                last list item of this argument.
                                the referenced data structure can contain immutable data node objects (like tuples and
                                strings) which will be accordingly changed/replaced if affected/needed.
                                at least one object/element, situated above of replaced data object within the deep data
                                structure, has to be mutable, else a :class:`ValueError` will be raised.
    :param new_value:           value to be assigned to the element referenced by the last list item of the argument in
                                :paramref:`.obj_keys`.
    :return:                    the number of levels of the first mutable data objects above the changed data object,
                                or 0 of the changed data object is mutable.
    :raises:                    `ValueError` if no immutable parent object got found or if the object key list in the
                                :paramref:`.obj_keys` argument is empty.
    """
    mutable_offset = 0
    obj = None
    for obj, key_or_attr in reversed(obj_keys):
        if isinstance(obj, (str, tuple)):
            new_value = (new_value, ) if isinstance(obj, tuple) else str(new_value)
            # noinspection unsupported-operator
            new_value = obj[:key_or_attr] + new_value + obj[key_or_attr + 1:]
            mutable_offset += 1
            continue

        if isinstance(obj, MUTABLE_DATA_TYPES):
            obj[key_or_attr] = new_value
        elif isinstance(key_or_attr, str):
            setattr(obj, key_or_attr, new_value)

        return mutable_offset

    raise ValueError(f"no mutable (parent) object found in {obj_keys=}; {mutable_offset} level(s) above of {obj=}")
