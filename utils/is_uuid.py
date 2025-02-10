import uuid


def is_uuid(value):
    try:
        uuid_obj = uuid.UUID(value)
        return True
    except ValueError:
        return False
