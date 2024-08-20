import os
from numpy._core.multiarray import result_type
import openai
import sys
import numpy as np
import pandas as pd

# Function to query OpenAI's API
def ask_openai(messages, temperature, model):
    # Ensure the API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")

    # Initialize OpenAI client using the API key
    client = openai.OpenAI(api_key=api_key)

    # Create the chat completion using the given parameters
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )

    # Return the content of the first choice's message properly
    if completion.choices and completion.choices[0].message:
        return completion.choices[0].message.content  # Accessing content directly
    else:
        return "No completion found."
temperature = 0
model = "gpt-4"
###################







# Inside Out: Esta funcion tiene como objetivo hacer preguntas abiertas, definir un camino y profundizar utilizando preguntas cerradas y finalmente dar un plan de acción
derivacion = 0

# Cargo los archivos
# Abre el archivo en modo lectura
with open('contexto/contexto.txt', 'r') as archivo:
    contexto = archivo.read()

with open('contexto/pregunta_abierta.txt', 'r') as archivo:
    pregunta_abierta = archivo.read()
    
df = pd.read_csv('contexto/preguntas.csv')
defi = pd.read_csv('contexto/plan_de_accion.csv')


#Continuo con definir la pregunta abierta (Inside)

respuesta_abierta = "Amigo: " + input(pregunta_abierta)
conversation_history = [{"role": "system", "content": contexto + pregunta_abierta+ ": "+ respuesta_abierta}]
#result = ask_openai(conversation_history, temperature, model)
mensaje_urgencia = "En base únicamente a la respuesta de mi amigo, necesitas hacerle más preguntas o ya podes concluir que tiene que hacerse alguna intervenciones medica. Respuestas: /0 si necesitas hacerle mas preguntas/, /1 si podes concluir que tiene que hacerse alguna intervenciones medica/, /Null si no entendes el mensaje de mi amigo/."

conversation_history.append({"role": "user", "content": mensaje_urgencia})
result = ask_openai(conversation_history, temperature, model)
#print(result)


if result == "1":
    mensaje_urgencia = "Podrias por favor contestarle con un mensaje formal oral que incluya respetando la siguiente estructura: 1) Nivel de urgencia; 2) Posible diagnostico; 3)Cuales intervenciones medicas le van a realizar;4)Que vaya al Hospital Zona Norte."
    conversation_history.append({"role": "user", "content": mensaje_urgencia})
    result = ask_openai(conversation_history, temperature, model)
    print(("\n") + result)
    sys.exit()

elif (result != "1" and result != "0"):
    # Solicitar más información
    respuesta_adicional = input("\nProporciona más detalles de tu cuadro: ")
    conversation_history.append({"role": "user", "content": "Amigo: " + respuesta_adicional})
    conversation_history.append({"role": "user", "content": mensaje_urgencia})

    # Segunda llamada a la API de OpenAI
    result = ask_openai(conversation_history, temperature, model)

else:
    #En base a la pregunta abierta, califico en tipos de triage
    mis_preguntas = df.to_numpy()
    mis_triages = df[['# Camino', 'Camino']].drop_duplicates()

    mensaje_def_triage = ", ".join([f"{row['# Camino']}. {row['Camino']}" for index, row in mis_triages.iterrows()])

    mensaje_def_triage = "Basado únicamente en la respuesta del paciente, cual de estas guardaias estas 100% seguro de que corresponde derivarlo?: "+mensaje_def_triage+" En caso de no estar seguro mandalo a la 10. Serias tan amable de responderme solamente con numeros la guardia?"
    #print(mensaje_def_triage)
    conversation_history.append({"role": "user", "content": mensaje_def_triage})
    result = ask_openai(conversation_history, temperature, model)
    derivacion = int(result)
    #print(derivacion)

    #if derivacion != 2:
    #    print("Andá a la guardia del Hospital Zona Norte")
    #    sys.exit()




cantidad_caminos = df['# Camino'].nunique()

#En base a la respuesta armo un vector de respuestas y arranco a completarlo preguntandole a GPT cuales estan contestadas en la respuesta abierta

# Filtrar el DataFrame para obtener el camino elegido
filtered_data = df[df['# Camino'] == derivacion]

# Verificar si el DataFrame filtrado no está vacío
if not filtered_data.empty:
    # Extraer el nombre del camino elegido
    camino_elegido = filtered_data['Camino'].iloc[0]
    # Imprimir el camino elegido
    print("\nTu padecimiento es", camino_elegido + ". \nPor favor contestame las siguientes preguntas:")
else:
    print("No se encontró un camino correspondiente para la derivación:", derivacion)
    sys.exit()

# Extraer el número de pregunta y la pregunta
extracted_questions_numerers = filtered_data[['# Pregunta']]
extracted_questions = filtered_data[['# Pregunta', 'Pregunta']]

# Convertir las columnas a listas primero
preguntas_lista = "\n".join(f"{row['# Pregunta']} {row['Pregunta']}" for _, row in extracted_questions.iterrows())
#print(preguntas_lista)

preguntas_lista_numeros = "\n".join(f"{row['# Pregunta']}" for _, row in extracted_questions.iterrows())

#print(preguntas_lista_numeros)

# Ahora puedes imprimir la lista de preguntas sin el # Camino ni el Camino

mensaje_def_triage = (
    "¿Cuáles de estas preguntas estás completamente seguro que tienen una respuesta explicita positiva o negativa? Basadas únicamente en el texto del paciente.\n"
    + preguntas_lista +
    "\nPodrías darme la lista separada con una coma y si ninguna tiene respuesta por favor un 0"
)
#print(mensaje_def_triage)

conversation_history.append({"role": "user", "content": mensaje_def_triage})
result = ask_openai(conversation_history, temperature, model) 
#print (result)

elementos = result.split(',')

if result == "0":
    print("")
    #print("Vector Vacio")
elif all(elemento.strip().isdigit() and 1 <= int(elemento.strip()) <= len(preguntas_lista_numeros) for elemento in elementos):
    print("")
    #print("Vector Lleno")
else:
    print("Fin de fiesta")
    sys.exit()


#mensaje_completo = f"{mensaje_def_triage}\n{preguntas_lista}"
mensaje_completo = "Podrías contestarme separado por comas y ordenado por cada una de las preguntas: Respuestas: /1 para las respuestas positivas/, /0 para las respuestas negativas/ y /Null para las que no tengas suficiente información por favor/"
#print(mensaje_completo)
conversation_history.append({"role": "user", "content": mensaje_completo})
result = ask_openai(conversation_history, temperature, model) 
#print(result)



#String con el status de cada pregunta 
mis_respuestas = result.split(',')
#print(mis_respuestas)

#Chequeo si es un vector binario


# Verificar que index esté dentro del rango de extracted_questions antes de acceder
for index, respuesta in enumerate(mis_respuestas):
    if respuesta.strip().lower() == "null":
        if index < len(extracted_questions):
            # Preguntar al usuario por la pregunta correspondiente
            pregunta_cerrada = extracted_questions.iloc[index]['Pregunta']
            respuesta_usuario_cerrada = input(f"{pregunta_cerrada}: ")
            if respuesta_usuario_cerrada in "si":
                mis_respuestas[index] = 1
                #print("Yeah baby")
            elif respuesta_usuario_cerrada in "no":
                mis_respuestas[index] = 0
                #print("Noa baby")
            else:
                conversation_history.append({"role": "user", "content": pregunta_cerrada + respuesta_usuario_cerrada + "Mi amigo contesto positivamente, en caso de que haya contestado positivo contestarme con el digito 1 caso negativo el digito 0 y en cualquier otro caso Null?"})
                #print(conversation_history)
                result = ask_openai(conversation_history, temperature, model)
                
                if result !="0" and result !="1":
                    #print(result)
                    respuesta_usuario_cerrada = input("¿Podrias darme mas contexto?")
                    conversation_history.append({"role": "user", "content": pregunta_cerrada + respuesta_usuario_cerrada + "Mi amigo contesto positivamente, en caso de que haya contestado positivo contestarme con el digito 1 caso negativo el digito 0 y en cualquier otro caso Null?"})
                    #print(conversation_history)
                    result = ask_openai(conversation_history, temperature, model)
                    if result !="0" and result !="1":
                        print("Disculpame pero no te entiendo, andá a la guardia del Hospital Zona Norte de San Nicolás")
                        
                        sys.exit()
                    else:
                        mis_respuestas[index] = int(result)
                else:
                    mis_respuestas[index] = int(result)

        else:
            print(f"Andá rápido a la guardia del Hospital Zona Norte.")
            sys.exit()
        
        
            
#print(mis_respuestas)
# Cálculo de la magnitud (norma) del vector
magnitud = len(mis_respuestas)

#print(f"La magnitud del vector es: {magnitud}")


#Busco la opinion y el plan de accion para una combinatoria de respuestas        

# Convertir la cadena de respuestas en una lista de caracteres
respuestas_normalizadas = list(map(str, mis_respuestas))
#print(respuestas_normalizadas)

# Crear la variable respuestas_aux y sumar los caracteres de cada uno de los elementos
respuestas_aux = ''.join(respuestas_normalizadas)

# Imprimir el resultado
#print(f"respuestas_aux: {respuestas_aux}")

'''# Crear una nueva lista para almacenar las respuestas convertidas a enteros
respuestas_convertidas = []

# Recorrer la lista y convertir cada respuesta
respuestas_string = ""
for i in range(len(respuestas_normalizadas)):
    respuestas_string = respuestas_string + respuestas_convertidas[i] 

# Imprimir las respuestas convertidas
print(respuestas_convertidas)
'''
'''

respuestas_normalizadas = ''.join(map(str, mis_respuestas)) #Normalizacion de respuestas
print(respuestas_normalizadas)

for i in range(len(respuestas_normalizadas)):
    respuestas_normalizadas[i] = int(respuestas_normalizadas[i])

print(mis_respuestas)
'''


'''
fila = defi[(defi.iloc[:, :len(respuestas_normalizadas)].astype(str).agg(''.join, axis=1) == respuestas_convertidas)] # BuscarH
opinion = fila['OPINION'].values[0] if not fila.empty else "No se encontró la opinión."
'''
respuestas_aux = respuestas_aux.replace(" ", "")

# Realizar la búsqueda en el DataFrame defi utilizando 'loc'
fila = defi.loc[defi['AUX'] == int(respuestas_aux)]  # Asegúrate de que 'AUX' y 'respuestas_aux' estén en el mismo tipo (int en este caso)
#print(fila)

# Obtener el valor de la columna 'OPINION'
opinion = fila['OPINION'].values[0] if not fila.empty else "No se encontró la opinión."

# Imprimir el resultado
#print(f"Opinión encontrada: {opinion}")

if opinion == "DERIVACION":
    print("\n"+ (opinion))
    mensaje_urgencia = "Podrias por favor contestarle a mi amigo con un mensaje a mi amigo con la siguiente estructura: Te voy a contar como estas: 1) Nivel de urgencia; 2) Posible diagnostico; 3) Plan de accion/intervenciones medicas a realizar; 4) Necesidad de ir al Hospital; recordar que el hospital asignado es el Hospital Zona Norte de San Nicolás, de ser necesario."
    
    conversation_history.append({"role": "user", "content": mensaje_urgencia})
    result = ask_openai(conversation_history, temperature, model)
    print(result)
    #print("Andá a la guardia del Hospital Zona Norte.")
    sys.exit()

if opinion != "DERIVACION":
    print("\n"+ (opinion))
    mensaje_urgencia = "Podrias por favor contestarle a mi amigo con un mensaje a mi amigo con la siguiente estructura: Te voy a contar como estas: 1) Nivel de urgencia; 2) Posible diagnostico; 3) Plan de accion/intervenciones medicas a realizar; 4) Necesidad de ir al Hospital; recordar que el hospital asignado es el Hospital Zona Norte de San Nicolás, de ser necesario."
    conversation_history.append({"role": "user", "content": mensaje_urgencia})
    result = ask_openai(conversation_history, temperature, model)
    print(("\n") + result)
    protocolo = fila['PROTOCOLO'].values[0] if not fila.empty else "No se encontró la opinión."
#print(f"\nTe recomiendo que sigas el siguiente plan de acción: {protocolo}")
#print("Andá a la guardia del Hospital Zona Norte.")

sys.exit()
