from aiogram.fsm.state import StatesGroup, State



class ClientCall(StatesGroup):   
    Help = State()
    


class RedactOrder(StatesGroup):
    Call = State()

    OrderState = State()

    ProductId = State()
    ProductPrice = State()
    ProductCount = State()

    OptionallyProductId = State()
    OptionallyProductPrice = State()
    OptionallyProductCount = State()

    Individual = State()

    Date = State()

    Payment = State()



class RedactProduct(StatesGroup):
    Category = State()

    SelectProduct = State()
    SelectOptProduct = State()

    ProductName = State()
    ProductPrice = State()
    ProductDes = State()
    ProductOpt = State()

    OptProductName = State()
    OptProductPrice = State()
    OptProductDes = State()

    Image = State()
    Video = State()



class CreateOrderFromHelp(StatesGroup):
    Call = State()

    ProductId = State()
    ProductCount = State()
    ProductPrice = State()

    OptionallyProductId = State()
    OptionallyProductPrice = State()
    OptionallyProductCount = State()

    Individual = State()

    Date = State()

    Request = State()
    Payment = State()


class AllOrders(StatesGroup):
    Category = State()

    OrderId = State()

    ChangeStatus = State()

    class RedactOrder(StatesGroup):
        Viewing = State()

        ProductId = State()
        ProductCount = State()
        ProductPrice = State()

        OptionallyProductId = State()
        OptionallyProductPrice = State()
        OptionallyProductCount = State()

        Individual = State()

        Date = State()
