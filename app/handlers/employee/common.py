from db import employee_requests, order_requests, product_requests



async def clearEmployeeDB(user_id):
  employee = await employee_requests.getEmployeeByUserId(user_id)
  print(employee)
  if not employee:
     return
  
  await employee_requests.updateBusyEmployee(employee.id, True)
  await employee_requests.updateActiveClientEmployee(employee.id, None)
  await employee_requests.updateActiveOrderEmployee(employee.id, None)


async def checkOrderProducts(order_id) -> bool:
   order = await order_requests.getOrderById(order_id)

   if not order:
      return False
   
   product = await product_requests.getProductById(order.product_id)

   if not product:
      return False
   
   # opt_product = await optionally_product_requests.getOptionallyProductById(order.optionally_product_id)

   # if not opt_product:
   #    return False
   
   # if not opt_product in product.optionally:
   #    return False
   

   return True




