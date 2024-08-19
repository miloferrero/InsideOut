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

#Lo primero que hago es darle a GPT contexto
contexto = "Sos un prestigioso medico del Mayo Clinic y tu mejor amigo se siente mal. Vos:"

#Continuo con definir la pregunta abierta (Inside)
pregunta_abierta = "Hola, me contas que te anda pasando con lujo de detalle: "

pregunta_abierta = input(pregunta_abierta)
pregunta_abierta = "Amigo: " + pregunta_abierta
conversation_history = [{"role": "system", "content": contexto + pregunta_abierta}]

#result = ask_openai(conversation_history, temperature, model)
mensaje_urgencia = "Con esta info podes determinar si tengo Escala de Severidad de Emergencias del 1 al 3 o hace falta hacer mas preguntas? Podrías por favor respondeme: //1 si tenes alguna sospecha de que sea ESI 1, 2 o 3// o //0 si no tenes ninguna sospecha//"
conversation_history.append({"role": "user", "content": mensaje_urgencia})
result = ask_openai(conversation_history, temperature, model)
#print(result)

if result != "1" and result != "0":
    print("X - Andá rápido a la guardia del Hospital Zona Norte")
    sys.exit()
if result == "1":
    print ("\nUrgencia - Andá rápido a la guardia del Hospital Zona Norte.")
    sys.exit()

#En base a la pregunta abierta, califico en tipos de triage
df = pd.read_csv('preguntas.csv')
mis_preguntas = df.to_numpy()
mis_triages = df[['# Camino', 'Camino']].drop_duplicates()

mensaje_def_triage = ", ".join([f"{row['# Camino']}. {row['Camino']}" for index, row in mis_triages.iterrows()])

mensaje_def_triage = "Basado únicamente en la respuesta del paciente, cual de estas guardaias estas 100% seguro de que corresponde derivarlo?: "+mensaje_def_triage+" En caso de no estar seguro mandalo a la 10. Serias tan amable de responderme solamente con numeros la guardia?"
#print(mensaje_def_triage)
conversation_history.append({"role": "user", "content": mensaje_def_triage})
result = ask_openai(conversation_history, temperature, model)
derivacion = int(result)
#print(result)

if derivacion != 2:
    print("Esta guardia todavía no esta desarrollada")
    sys.exit()


#cantidad_caminos = df['# Camino'].nunique()

#En base a la respuesta armo un vector de respuestas y arranco a completarlo preguntandole a GPT cuales estan contestadas en la respuesta abierta

# Asumiendo que 'Pregunta' es la columna que contiene las preguntas
filtered_data = df[df['# Camino'] == derivacion]
#print(filtered_data)

# Extraer el número de pregunta y la pregunta
extracted_questions = filtered_data[['# Pregunta', 'Pregunta']]

# Convertir las columnas a listas primero
preguntas_lista = "\n".join(f"{row['# Pregunta']} {row['Pregunta']}" for _, row in extracted_questions.iterrows())
#print(preguntas_lista)



# Ahora puedes imprimir la lista de preguntas sin el # Camino ni el Camino

mensaje_def_triage = (
    "Basado en la respuesta del paciente, ¿cuáles de estas preguntas estás 100% seguro que tienen una respuesta?\n"
    + preguntas_lista +
    "\n¿Si ninguna tiene respuesta, podrias responder espacio en blanco?"
)
#print(mensaje_def_triage)

conversation_history.append({"role": "user", "content": mensaje_def_triage})
result = ask_openai(conversation_history, temperature, model) 
#print(result)

#mensaje_completo = f"{mensaje_def_triage}\n{preguntas_lista}"
mensaje_completo = "Podrías contestarme separado por comas y ordenado por cada una de las preguntas: 1 para las respuestas positivas, 0 para las respuestas negativas y Null para las que no estan explicitamente"
#print(mensaje_completo)


conversation_history.append({"role": "user", "content": mensaje_completo})
result = ask_openai(conversation_history, temperature, model) 

#String con el status de cada pregunta 
mis_respuestas = result.split(',')
#print(mis_respuestas)

# Verificar que index esté dentro del rango de extracted_questions antes de acceder
for index, respuesta in enumerate(mis_respuestas):
    if respuesta.strip().lower() == "null":
        if index < len(extracted_questions):
            # Preguntar al usuario por la pregunta correspondiente
            pregunta_cerrada = extracted_questions.iloc[index]['Pregunta']
            respuesta_usuario_cerrada = input(f"{pregunta_cerrada}: ")
        else:
            print(f"Andá rápido a la guardia del Hospital Zona Norte.")
            sys.exit()

        conversation_history = [{"role": "system", "content": pregunta_cerrada + respuesta_usuario_cerrada + "Mi amigo contesto positivamente, en caso de que haya contestado positivo contestarme con el digito 1 caso contrario el digito 0?"}]
        result = ask_openai(conversation_history, temperature, model)
        mis_respuestas[index] = result
print(mis_respuestas)    

mis_respuestas[index] = result.strip()
#print(mis_respuestas)

        
        
            
#Busco la opinion y el plan de accion para una combinatoria de respuestas        

    
# Cargar el archivo CSV
defi = pd.read_csv('plan_de_accion.csv')  # Asegúrate de especificar la ruta correcta al archivo CSV

respuestas_normalizadas = ''.join(map(str, mis_respuestas)) #Normalizacion de respuestas
fila = defi[(defi.iloc[:, :7].astype(str).agg(''.join, axis=1) == respuestas_normalizadas)] # BuscarH
opinion = fila['OPINION'].values[0] if not fila.empty else "No se encontró la opinión."
#print(f"Opinión: {opinion}")

protocolo = fila['PROTOCOLO'].values[0] if not fila.empty else "No se encontró la opinión."
print(f"\nTe recomiendo que sigas el siguiente plan de acción: {protocolo}")
sys.exit()



'''
if not result.empty:
    opinion_recomendada = result['OPINION'].values[0]
    plan_accion_recomendado = result['PROTOCOLO'].values[0]
    print(f"Opinión recomendada: {opinion_recomendada}")
    print(f"Plan de acción recomendado: {plan_accion_recomendado}")
else:
    print("No se encontró un protocolo específico para esta combinación de respuestas.")
'''





'''

conversation_history.append({"role": "user", "content": "me pasarías el numero de tipo de triage"})


if "0" in result:
    mis_triages[0] = "AUH"
    print(mis_triages[0])
    sys.exit()
if "1" in result:
    mis_triages[1] = "Bienvenido a la guardia respiratoria"
    print(mis_triages[1])
if "2" in result:
    mis_triages[2] = "Guardia no respiratoria"
    print(mis_triages[2])
    sys.exit()

# Triage respiratorio
conversation_history.append({"role": "user", "content": "Basado únicamente en mi mensaje, cuales de estas preguntas estas 100% seguro que tienen una respuesta explicita: 0.⁠ ⁠Tenes fiebre mayor a 38? 1.⁠ ⁠Tenes tos con sangre? 2. ⁠Tenes tos seca? 3.⁠ ⁠Tenes dolor de garganta? 4.⁠ ⁠Tenes problemas para hablar? 5. Hace mas de 10 días que te sentis asi?"})


conversation_history.append({"role": "user", "content": "me pasarías unicamente los numeros de preguntas sin respuesta explicita separados por comas?"})
result = ask_openai(conversation_history, temperature, model)
preguntas_sin_respuesta = result
print(preguntas_sin_respuesta)

#Pregunto las preguntas que no respondió explicitamente
if "0" in preguntas_sin_respuesta:
    respuesta_0= input("⁠Tenes fiebre mayor a 38?: ")
    conversation_history.append({"role": "user", "content": "Tenes fiebre mayor a 38?: " + respuesta_1 + "Basado únicamente en mi mensaje, podrías estar 100% seguro que tienen una respuesta explicita: para ? Tenes fiebre mayor a 38?"})
    conversation_history.append({"role": "user", "content":"Podrías escribir 1 si la respuesta fue positiva o 0 si fue negativa"})
    result = ask_openai(conversation_history, temperature, model)
    i = 1
    mis_answers [0] = result
    print(mis_answers [0])

if "2" in preguntas_sin_respuesta:
    respuesta_2 = input("2.⁠ ⁠Tenes tos con sangre?")
    conversation_history.append({"role": "user", "content": "1.⁠ ⁠Tenes fiebre mayor a 38?: " + respuesta_2 + "Basado únicamente en mi mensaje, podrías estar 100% seguro que tienen una respuesta explicita: para ? 2.⁠ ⁠Tenes tos con sangre?"})
    conversation_history.append({"role": "user", "content":"Podrías escribir 1 si la respuesta fue positiva o 0 si fue negativa"})
    result = ask_openai(conversation_history, temperature, model)
    mis_answers [2] = result
    print(mis_answers [1])


if "3" in preguntas_sin_respuesta:
    respuesta_3 = input("3. ⁠Tenes tos seca?")
if "4" in preguntas_sin_respuesta:
    respuesta_4 = input("4.⁠ ⁠Tenes dolor de garganta?")
if "5" in preguntas_sin_respuesta:
    respuesta_5 = input("5.⁠ ⁠Tenes problemas para hablar? ")
if "6" in preguntas_sin_respuesta:
    respuesta_6 = input("6. Hace mas de 10 días que te sentis asi?")
    '''
