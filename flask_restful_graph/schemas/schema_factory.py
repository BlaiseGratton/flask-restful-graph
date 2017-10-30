from py2neo.ogm import Property
import stringcase


registered_models = {}


def register_model_property(model_key, prop_name, marshal_property, **kwargs):
    try:
        model = registered_models[model_key]
    except KeyError:
        model = {}
        registered_models[model_key] = model

    # by default, (un)marshal every property to/from camelcased form
    if 'load_from' not in kwargs and 'dump_to' not in kwargs:
        camelcased = stringcase.camelcase(prop_name)
        model[prop_name] = marshal_property(
                load_from=camelcased, dump_to=camelcased, **kwargs)
    else:
        model[prop_name] = marshal_property(**kwargs)

    return Property()


def build_schemas():
    return registered_models
