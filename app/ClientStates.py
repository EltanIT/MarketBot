from aiogram.fsm.state import StatesGroup, State



class CreateOrder(StatesGroup):
    ProductCount = State()   
    OptionallProductCount = State()

    Fio = State()
    PhoneNumber = State()
    Address = State()
    AboutDelivery = State()

    RedactOrder = State()

    VerifyPhoto = State()
    VerifyVideo = State()


class CreateOrderFromEmployee(StatesGroup):
    Fio = State()
    PhoneNumber = State()
    Address = State()
    AboutDelivery = State()

    RedactOrderState = State()


    class RedactOrder(StatesGroup):
        Fio = State()
        PhoneNumber = State()
        Address = State()
        AboutDelivery = State()


class RedactOrder(StatesGroup):
    Fio = State()
    PhoneNumber = State()
    Address = State()
    AboutDelivery = State()


class EmployeeCall(StatesGroup):
    Call = State()
    DescriptionProduct = State()


class SelectProduct(StatesGroup):
    Product = State()
    AboutProduct = State()
    BeforeOrdering = State()
    OptionallyProduct = State()

    IndividualProduct = State()


class OrderComment(StatesGroup):
    Comment = State()
    Rating = State()


class RedactOldOrder(StatesGroup):
    OrderId = State()

    AboutOrder = State()
