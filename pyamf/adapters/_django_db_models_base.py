# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
`django.db.models` adapter module.

:see: `Django Project <http://www.djangoproject.com>`_

:since: 0.4.1
"""

from django.db.models.base import Model
from django.db.models import fields
from django.db.models.fields import related, files

import datetime

import pyamf
from pyamf.util import imports


class DjangoReferenceCollection(dict):
    """
    This helper class holds a dict of klass to pk/objects loaded from the
    underlying db.

    :since: 0.5
    """

    def _getClass(self, klass):
        if klass not in self.keys():
            self[klass] = {}

        return self[klass]

    def getClassKey(self, klass, key):
        """
        Return an instance based on klass/key.

        If an instance cannot be found then `KeyError` is raised.

        :param klass: The class of the instance.
        :param key: The primary_key of the instance.
        :return: The instance linked to the `klass`/`key`.
        :rtype: Instance of `klass`.
        """
        d = self._getClass(klass)

        return d[key]

    def addClassKey(self, klass, key, obj):
        """
        Adds an object to the collection, based on klass and key.

        :param klass: The class of the object.
        :param key: The datastore key of the object.
        :param obj: The loaded instance from the datastore.
        """
        d = self._getClass(klass)

        d[key] = obj


class DjangoClassAlias(pyamf.ClassAlias):

    def getCustomProperties(self):
        self.fields = {}
        self.relations = {}
        self.columns = []

        self.meta = self.klass._meta

        for name in self.meta.get_all_field_names():
            x = self.meta.get_field_by_name(name)[0]

            if isinstance(x, files.FileField):
                self.readonly_attrs.update([name])

            if isinstance(x, related.RelatedObject):
                continue

            if not isinstance(x, related.ForeignKey):
                self.fields[name] = x
            else:
                self.relations[name] = x

        for k, v in self.klass.__dict__.iteritems():
            if isinstance(v, related.ReverseManyRelatedObjectsDescriptor):
                self.fields[k] = v.field

        parent_fields = []

        for field in self.meta.parents.values():
            parent_fields.append(field.attname)
            del self.relations[field.name]

        self.exclude_attrs.update(parent_fields)

        props = self.fields.keys()

        self.encodable_properties.update(props)
        self.decodable_properties.update(props)

    def _compile_base_class(self, klass):
        if klass is Model:
            return

        pyamf.ClassAlias._compile_base_class(self, klass)

    def _encodeValue(self, field, value):
        if value is fields.NOT_PROVIDED:
            return pyamf.Undefined

        if value is None:
            return value

        # deal with dates ..
        if isinstance(field, fields.DateTimeField):
            return value
        elif isinstance(field, fields.DateField):
            return datetime.datetime(value.year, value.month, value.day, 0, 0, 0)
        elif isinstance(field, fields.TimeField):
            return datetime.datetime(1970, 1, 1,
                value.hour, value.minute, value.second, value.microsecond)
        elif isinstance(value, files.FieldFile):
            return value.name

        return value

    def _decodeValue(self, field, value):
        if value is pyamf.Undefined:
            return fields.NOT_PROVIDED

        if isinstance(field, fields.AutoField) and value == 0:
            return None
        elif isinstance(field, fields.DateTimeField):
            # deal with dates
            return value
        elif isinstance(field, fields.DateField):
            if not value:
                return None

            return datetime.date(value.year, value.month, value.day)
        elif isinstance(field, fields.TimeField):
            if not value:
                return None

            return datetime.time(value.hour, value.minute, value.second, value.microsecond)

        return value

    def getEncodableAttributes(self, obj, **kwargs):
        attrs = pyamf.ClassAlias.getEncodableAttributes(self, obj, **kwargs)

        if not attrs:
            attrs = {}

        for name, prop in self.fields.iteritems():
            if name not in attrs.keys():
                continue

            if isinstance(prop, related.ManyToManyField):
                attrs[name] = [x for x in getattr(obj, name).all()]
            else:
                attrs[name] = self._encodeValue(prop, getattr(obj, name))

        keys = attrs.keys()

        for key in keys:
            if key.startswith('_'):
                del attrs[key]

        for name, relation in self.relations.iteritems():
            if '_%s_cache' % name in obj.__dict__:
                attrs[name] = getattr(obj, name)

            del attrs[relation.column]

        if not attrs:
            attrs = None

        return attrs

    def getDecodableAttributes(self, obj, attrs, **kwargs):
        attrs = pyamf.ClassAlias.getDecodableAttributes(self, obj, attrs, **kwargs)

        for n in self.decodable_properties:
            if n in self.relations:
                continue

            f = self.fields[n]

            attrs[f.attname] = self._decodeValue(f, attrs[n])

        # primary key of django object must always be set first for
        # relationships with other model objects to work properly
        # and dict.iteritems() does not guarantee order
        #
        # django also forces the use only one attribute as primary key, so
        # our obj._meta.pk.attname check is sufficient)
        try:
            setattr(obj, obj._meta.pk.attname, attrs[obj._meta.pk.attname])
            del attrs[obj._meta.pk.attname]
        except KeyError:
            pass

        return attrs


def getDjangoObjects(context):
    """
    Returns a reference to the `django_objects` on the context. If it doesn't
    exist then it is created.

    :param context: The context to load the `django_objects` index from.
    :type context: Instance of :class:`pyamf.BaseContext`
    :return: The `django_objects` index reference.
    :rtype: Instance of :class:`DjangoReferenceCollection`
    :since: 0.5
    """
    if not hasattr(context, 'django_objects'):
        context.django_objects = DjangoReferenceCollection()

    return context.django_objects


def writeDjangoObject(self, obj, *args, **kwargs):
    """
    The Django ORM creates new instances of objects for each db request.
    This is a problem for PyAMF as it uses the id(obj) of the object to do
    reference checking.

    We could just ignore the problem, but the objects are conceptually the
    same so the effort should be made to attempt to resolve references for a
    given object graph.

    We create a new map on the encoder context object which contains a dict of
    C{object.__class__: {key1: object1, key2: object2, .., keyn: objectn}}. We
    use the primary key to do the reference checking.

    :since: 0.5
    """
    if not isinstance(obj, Model):
        self.writeNonDjangoObject(obj, *args, **kwargs)

        return

    context = self.context
    kls = obj.__class__

    s = obj.pk

    if s is None:
        self.writeNonDjangoObject(obj, *args, **kwargs)

        return

    django_objects = getDjangoObjects(context)

    try:
        referenced_object = django_objects.getClassKey(kls, s)
    except KeyError:
        referenced_object = obj
        django_objects.addClassKey(kls, s, obj)

    self.writeNonDjangoObject(referenced_object, *args, **kwargs)


def install_django_reference_model_hook(mod):
    """
    Called when :module:`pyamf.amf0` or :module:`pyamf.amf3` are imported. Attaches the
    :func:`writeDjangoObject` method to the `Encoder` class in that module.

    :param mod: The module imported.
    :since: 0.4.1
    """
    if not hasattr(mod.Encoder, 'writeNonDjangoObject'):
        mod.Encoder.writeNonDjangoObject = mod.Encoder.writeObject
        mod.Encoder.writeObject = writeDjangoObject


# initialise the module here: hook into pyamf

pyamf.register_alias_type(DjangoClassAlias, Model)

# hook the L{writeDjangobject} method to the Encoder class on import
imports.when_imported('pyamf.amf0', install_django_reference_model_hook)
imports.when_imported('pyamf.amf3', install_django_reference_model_hook)
