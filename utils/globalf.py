# Importa el módulo re para trabajar con expresiones regulares, aunque no se usa en esta función.
import re  

# Define una función para validar posibles inyecciones SQL en los datos de entrada.
def validate_sql_injection(data):  
    # Define una lista de palabras clave peligrosas que podrían indicar una inyección SQL.
    dangerous_keywords = ["exec", "EXEC", "select", "SELECT"]  
    
    # Verifica si alguna de las palabras clave peligrosas está presente en los datos.
    if any(keyword in data for keyword in dangerous_keywords):  
        # Devuelve True si se encuentra alguna palabra clave peligrosa.
        return True  

    # Verifica si los datos contienen caracteres especiales que podrían ser usados en inyecciones SQL.
    if any(char in data for char in ["'", ";", "--", "/*", "*/", "@", "`", '"']):  
        # Devuelve True si se encuentran caracteres especiales peligrosos.
        return True  

    # Devuelve False si no se detectan palabras clave ni caracteres especiales peligrosos.
    return False  
