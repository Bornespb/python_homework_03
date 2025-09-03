from datetime import date, datetime
import re
import hashlib
from abc import abstractmethod, ABC
from .scoring import get_score, get_interests

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"


class BaseValidatedField(ABC):
    def __init__(self, required: bool = False, nullable: bool = False):
        self.required = required
        self.nullable = nullable
        self.name = None
        self.value = None

    def __set_name__(self, owner, name):
        self.name = name

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "validate" not in cls.__dict__:
            raise TypeError(f"Class {cls.__name__} must have a validate method")

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        is_valid, error = self.validate(value)
        if not is_valid:
            raise ValueError(f"Invalid field value for {self.name}: {error}")
        self.value = value

    @abstractmethod
    def validate(self, value) -> tuple[bool, str | None]:
        pass


class CharField(BaseValidatedField):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable)

    def validate(self, value: str | None) -> tuple[bool, str | None]:
        if self.required and value is None:
            return False, f"{self.name} is required"
        if not self.required and value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"{self.name} must be a string"
        if not self.nullable and value == "":
            return False, f"{self.name} must be a non empty string"
        return True, None


class ArgumentsField(BaseValidatedField):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable)

    def validate(self, value: dict | None) -> tuple[bool, str | None]:
        if self.required and value is None:
            return False, f"{self.name} is required"
        if not isinstance(value, dict):
            return False, f"{self.name} must be a dictionary"
        if not self.nullable and value == {}:
            return False, f"{self.name} must be a non empty dictionary"
        return True, None


class EmailField(CharField):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable)

    def __set__(self, instance, value):
        super().__set__(instance, value)

    def validate(self, value: str | None) -> tuple[bool, str | None]:
        is_valid, error = super().validate(value)
        if not is_valid:
            return is_valid, error
        value = str(value)
        if "@" not in value:
            return False, f"{self.name} must be a valid email"
        return True, None


class PhoneField(BaseValidatedField):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable)

    def validate(self, value: str | int | None) -> tuple[bool, str | None]:
        if self.required and value is None:
            return False, f"{self.name} is required"
        if not isinstance(value, str) and not isinstance(value, int):
            return False, f"{self.name} must be a string or an integer"
        if isinstance(value, int):
            parsed_value = int(value)
            if not self.nullable and parsed_value == 0:
                return False, f"{self.name} must be a non emptyvalid phone number"
            if parsed_value < 70000000000 or parsed_value > 79999999999:
                return False, f"{self.name} must be a valid phone number"
            return True, None
        value = str(value)
        if not self.nullable and value == "":
            return False, f"{self.name} must be a non empty valid phone number"
        if not value.startswith("7") or not len(value) == 11:
            return False, f"{self.name} must be a valid phone number"
        return True, None


class DateField(BaseValidatedField):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable)

    def validate(self, value: str | None) -> tuple[bool, str | None]:
        if self.required and value is None:
            return False, f"{self.name} is required"
        value = str(value)
        if not re.match(r"\d{2}\.\d{2}\.\d{4}", value):
            return False, f"{self.name} must be a valid date"
        parsed_date = datetime.strptime(value, "%d.%m.%Y")
        if not self.nullable and parsed_date == date.min:
            return False, f"{self.name} must be a non empty date"
        return True, None


class BirthDayField(DateField):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable)

    def validate(self, value: str | None) -> tuple[bool, str | None]:
        is_valid, error = super().validate(value)
        if not is_valid:
            return is_valid, error
        value = str(value)
        parsed_date = datetime.strptime(value, "%d.%m.%Y")
        if not parsed_date.year > datetime.now().year - 70:
            return False, f"{self.name} must be less than 70 years old"
        return True, None


class GenderField(BaseValidatedField):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable)

    def validate(self, value: int | None) -> tuple[bool, str | None]:
        if self.required and value is None:
            return False, f"{self.name} is required"
        if not isinstance(value, int):
            return False, f"{self.name} must be an integer"
        if value not in [0, 1, 2]:
            return False, f"{self.name} must be 0, 1 or 2"
        return True, None


class ClientIDsField(BaseValidatedField):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable)

    def validate(self, value: list[int] | None) -> tuple[bool, str | None]:
        if self.required and value is None:
            return False, f"{self.name} is required"
        if not isinstance(value, list) or not all(
            isinstance(item, int) for item in value
        ):
            return False, f"{self.name} must be a list of integers"
        if not self.nullable and value == []:
            return False, f"{self.name} must be a non empty list of integers"
        return True, None


class BaseRequest(ABC):
    @abstractmethod
    def execute(self):
        pass


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def __init__(self, data: dict) -> None:
        self.client_ids = data.get("client_ids", None)
        self.date = data.get("date", None)

    def execute(self) -> dict:
        return {
            client_id: get_interests(store=None, cid=client_id)
            for client_id in self.client_ids
        }


class OnlineScoreRequest(BaseRequest):
    phone = PhoneField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, data: dict) -> None:
        self.phone = data.get("phone", None)
        self.email = data.get("email", None)
        self.first_name = data.get("first_name", None)
        self.last_name = data.get("last_name", None)
        self.birthday = data.get("birthday", None)
        self.gender = data.get("gender", None)

    def validate(self):
        if self.phone and self.email:
            return True
        if self.first_name and self.last_name:
            return True
        if self.gender and self.birthday:
            return True
        return False

    def execute(self) -> dict:
        if not self.validate():
            raise ValueError("Invalid arguments")
        return {
            "score": get_score(
                store=None,
                phone=self.phone,
                email=self.email,
                first_name=self.first_name,
                last_name=self.last_name,
                birthday=self.birthday,
                gender=self.gender,
            )
        }


class MethodRequest:
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)

    def __init__(self, data: dict):
        self.body = data.get("body", {})
        self.account = self.body.get("account", None)
        self.login = self.body.get("login", None)
        self.token = self.body.get("token", None)
        self.arguments = self.body.get("arguments", None)
        self.method = self.body.get("method", None)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def check_auth(self):
        if self.is_admin:
            digest = hashlib.sha512(
                (datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode("utf-8")
            ).hexdigest()
        else:
            account = self.account if self.account else ""
            digest = hashlib.sha512(
                (account + self.login + SALT).encode("utf-8")
            ).hexdigest()
        return digest == self.token
