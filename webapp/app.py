from flask import Flask, request, render_template, jsonify, url_for
import joblib
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)

# Cargar el modelo ajustado
models = {
    "XGBoostPedidosDeManana": joblib.load('models/XGBoostPedidosDeManana_Ajustado.joblib')
}

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    form_data = {}

    if request.method == "POST":
        print("Datos recibidos del formulario:", request.form)
        try:
            # Obtener la fecha seleccionada
            fecha_str = request.form.get("fecha")
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            numero_semana = fecha.isocalendar()[1]

            # Determinar si es fin de semana
            is_weekend = 1 if fecha.weekday() in [5, 6] else 0

            # Determinar si es período de vacaciones
            es_vacaciones = 1 if 32 <= numero_semana <= 35 else 0

            # Obtener otros datos del formulario
            form_data['prcp_actual'] = float(request.form.get("prcp_actual", 0))
            form_data['prcp_anterior'] = float(request.form.get("prcp_anterior", 0))
            form_data['prcp_dia_2'] = float(request.form.get("prcp_dia_2", 0))
            form_data['prcp_dia_3'] = float(request.form.get("prcp_dia_3", 0))
            form_data['prcp_dia_4'] = float(request.form.get("prcp_dia_4", 0))
            form_data['prcp_dia_5'] = float(request.form.get("prcp_dia_5", 0))

            
            form_data['orders_lag1'] = int(request.form.get("orders_lag1", 0))
            form_data['orders_lag2'] = int(request.form.get("orders_lag2", 0))

            # Calcular características
            prcp_media = (form_data['prcp_actual'] + form_data['prcp_anterior']) / 2
            pesos = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
            pesos = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
            prcp_ponderada = sum([
               form_data['prcp_actual'] * pesos[5],
               form_data['prcp_anterior'] * pesos[4],
               form_data['prcp_dia_2'] * pesos[3],
               form_data['prcp_dia_3'] * pesos[2],
               form_data['prcp_dia_4'] * pesos[1],
               form_data['prcp_dia_5'] * pesos[0]
])


            features = [[
                prcp_media,
                prcp_ponderada,
                int(prcp_media > 100),
                es_vacaciones,
                1.3 if form_data['prcp_actual'] > 25 else 1,
                form_data['orders_lag1'],
                form_data['orders_lag2'],
                is_weekend
            ]]

            # Depuración: imprimir las características
            print("Características enviadas al modelo:", features)

            # Predicción del modelo
            base_prediction = models['XGBoostPedidosDeManana'].predict(features)[0]
            print("Predicción inicial del modelo:", base_prediction)

            # Aplicar ajustes
            # Aplicar ajustes por fin de semana
            if is_weekend == 1:
              if fecha.weekday() == 6:  # Domingo
                 base_prediction = base_prediction * 0.144
              elif fecha.weekday() == 5:  # Sábado
                 base_prediction = base_prediction * 0.272

            if es_vacaciones == 1:
                base_prediction *= 0.66

            prediction = max(base_prediction, 0)
            print("Predicción final después de ajustes:", prediction)

            if prediction and 'fecha' in locals():
                try:
                    response = requests.post(
                        url_for('guardar', _external=True),
                        json={'fecha': fecha_str, 'prediction': int(round(prediction))}
                        )
                    print("Respuesta del guardado en el servidor:", response.json())
                except Exception as e:
                    print("Error al intentar guardar la prediccion:", e)
                    raise


        except Exception as e:
            prediction = f"Error: {e}"
            print("Error durante la predicción:", e)

    return render_template("index.html", prediction=prediction, form_data=form_data, numero_semana=numero_semana if 'fecha' in locals() else None)

# Ruta para guardar datos en la base de datos
@app.route('/guardar', methods=['POST'])
def guardar():
    data = request.json
    print("Datos recibidos para guardar:", data)
    fecha = data.get('fecha')
    prediction = data.get('prediction')

    if not fecha or not prediction:
        return jsonify({'error': 'Datos no válidos'}), 400

    conn = sqlite3.connect('historico.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO historico (fecha, prediction) VALUES (?, ?)', (fecha, prediction))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Datos guardados correctamente'}), 200

# Ruta para obtener el histórico de la base de datos
@app.route('/historico', methods=['GET'])
def ver_historico():
    conn = sqlite3.connect('historico.db')
    cursor = conn.cursor()
    cursor.execute('SELECT fecha, prediction FROM historico')
    rows = cursor.fetchall()
    print("Datos recuperados del historico:", rows)
    conn.close()

    historico = [{'fecha': row[0], 'prediction': int(round(row[1]))} for row in rows]
    return jsonify(historico)


if __name__ == "__main__":
    app.run(debug=False)




