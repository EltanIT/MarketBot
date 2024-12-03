from enum import Enum

class UserRole(Enum):
    CLIENT = 'CLIENT'
    EMPLOYEE = 'EMPLOYEE'
    ADMIN = 'ADMIN'



class OrderStatus(Enum):

    DURING_VERIFY = 'ОЖИДАЕТ ВЕРИФИКАЦИИ', 1, '➖'
    DURING_PAYMENT = 'ОЖИДАЕТ ОПЛАТЫ', 2, '💸'
    DURING_PROCESSING = 'В ПРОЦЕССЕ ОБРАБОТКИ', 3, '🕔'
    SENT = 'ОТПРАВЛЕН', 4, '📦'
    DELIVERED = 'ДОСТАВЛЕН', 5, '✅'

    CANCEL = 'ОТМЕНЕН', 6, '❌'


    
    


class AppName(Enum):
    TG = 'TG'
    VK = 'VK'


class DeliveryMethod(Enum):
    SDAK = 'СДЭК/ТК "Энергия"'
    PICKUP = 'САМОВЫВОЗ'