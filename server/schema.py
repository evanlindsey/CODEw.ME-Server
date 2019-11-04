from marshmallow import Schema, fields


class Code(Schema):
    js = fields.Str()
    html = fields.Str()
    css = fields.Str()


class Keys(Schema):
    room = fields.Str()
    repo = fields.Str()


class ClientID(Schema):
    id = fields.Str()


class ClientCode(Schema):
    id = fields.Str()
    code = fields.Str()
    lang = fields.Str()


class ClientTheme(Schema):
    id = fields.Str()
    theme = fields.Str()


class ClientDetails(Schema):
    id = fields.Str()
    code = fields.Nested(Code())
    theme = fields.Str()
