from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
from dateutil import parser
import mysql.connector
import uuid

app = Flask(__name__)
CORS(app)
""" CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}) """

# Configuración de la conexión a la base de datos
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="sistema_ticket"
)
cursor = db.cursor()

# Aqui valido las fechas
def validate_dates(start_date, end_date):
    current_date = datetime.now()
    if start_date < current_date:
        return "La fecha inicial no puede ser menor a la fecha actual."
    if end_date < start_date:
        return "La fecha final no puede ser anterior a la de inicio."
    return None

# Ruta para crear un evento
@app.route('/create_event', methods=['POST'])
def create_event():
    data = request.get_json()

    name = data.get("name")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    total_tickets_str = data.get("total_tickets")

    #convierto las fechas de string a objeto datetime
    try:
        start_date = parser.parse(start_date_str)
        end_date = parser.parse(end_date_str)
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido."}), 400

    #Validi las fechas
    error_message = validate_dates(start_date, end_date)
    if error_message:
        return jsonify({"error": error_message}), 400

    try:
        total_tickets = int(total_tickets_str)
    except ValueError:
        return jsonify({"error": "La cantidad de boletos debe ser un número entero."}), 400

    if not (1 <= total_tickets <= 300):
        return jsonify({"error": "El número de boletos debe ser entre 1 y 300."}), 400

    query = "INSERT INTO eventos (name, start_date, end_date, total_tickets) VALUES (%s, %s, %s, %s)"
    values = (name, start_date, end_date, total_tickets)

    try:
        cursor.execute(query, values)
        db.commit()
        return jsonify({"message": "Evento creado exitosamente."}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

# Ruta para editar un evento
@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json()

    name = data.get("name")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    total_tickets_str = data.get("total_tickets")

    #convierto las fechas de string a objeto datetime
    try:
        start_date = parser.parse(start_date_str) if start_date_str else None
        end_date = parser.parse(end_date_str) if end_date_str else None
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido."}), 400

    #aqui valido fechas
    if start_date or end_date:
        error_message = validate_dates(start_date or datetime.now(), end_date or datetime.now())
        if error_message:
            return jsonify({"error": error_message}), 400

    #aqui valido el total_tickets
    try:
        total_tickets = int(total_tickets_str) if total_tickets_str else None
    except ValueError:
        return jsonify({"error": "La cantidad de boletos debe ser un número entero."}), 400

    #obtengo el evento actual
    cursor.execute("SELECT total_tickets, sold_tickets FROM eventos WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    if not event:
        return jsonify({"error": "El evento no existe."}), 404

    current_total_tickets, sold_tickets = event

    #valido los boletos y si total_tickets cambia
    if total_tickets is not None:
        if total_tickets < sold_tickets:
            return jsonify({
                "error": f"No puedes reducir los boletos a menos de los ya vendidos ({sold_tickets})."
            }), 400

    #actualizo el evento en la base de datos
    query = """
        UPDATE eventos
        SET name = %s, start_date = %s, end_date = %s, total_tickets = %s
        WHERE id = %s
    """
    values = (
        name or event[0],  #uso el nombre actual si no se ingresa uno nuevo
        start_date or event[1],
        end_date or event[2],
        total_tickets or current_total_tickets,
        event_id,
    )

    try:
        cursor.execute(query, values)
        db.commit()
        return jsonify({"message": "Evento actualizado exitosamente."}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

# Ruta para mostrar los eventos
@app.route('/events', methods=['GET'])
def list_events():
    try:
        cursor.execute("SELECT id, name, start_date, end_date, total_tickets, sold_tickets FROM eventos")
        events = cursor.fetchall()
        events_list = [
            {
                "id": event[0],
                "name": event[1],
                "start_date": event[2].strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": event[3].strftime("%Y-%m-%d %H:%M:%S"),
                "total_tickets": event[4],
                "sold_tickets": event[5]
            }
            for event in events
        ]
        return jsonify(events_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para eliminar un evento
@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    #Aqui obtengo el evento desde la base de datos
    cursor.execute("SELECT start_date, end_date, sold_tickets FROM eventos WHERE id = %s", (event_id,))
    event = cursor.fetchone()

    if not event:
        return jsonify({"error": "Evento no encontrado."}), 404

    end_date, sold_tickets = event[1], event[2]
    current_date = datetime.now()

    #verifico si ya paso la fecha final del evento o si no hay boletos vendidos
    if end_date < current_date or sold_tickets == 0:
        try:
            # elimino el evento de la base de datos
            cursor.execute("DELETE FROM eventos WHERE id = %s", (event_id,))
            db.commit()
            return jsonify({"message": "Evento eliminado exitosamente."}), 200
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No puedes eliminar el evento porque no ha pasado su fecha de fin o tiene boletos vendidos."}), 400

# Ruta para vender un boleto de evento
@app.route('/sell_ticket/<int:event_id>', methods=['POST'])
def sell_ticket(event_id):
    #aqui verifico que el evento exista
    cursor.execute("SELECT total_tickets, sold_tickets FROM eventos WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    if not event:
        return jsonify({"error": "Evento no encontrado."}), 404

    total_tickets, sold_tickets = event

    if sold_tickets >= total_tickets:
        return jsonify({"error": "Ya no hay boletos disponibles."}), 400

    ticket_code = str(uuid.uuid4())

    query = "INSERT INTO boletos (event_id, ticket_code) VALUES (%s, %s)"
    values = (event_id, ticket_code)

    try:
        cursor.execute(query, values)
        db.commit()

        cursor.execute("UPDATE eventos SET sold_tickets = sold_tickets + 1 WHERE id = %s", (event_id,))
        db.commit()

        return jsonify({"message": "Boleto vendido exitosamente.", "ticket_code": ticket_code}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

# Ruta para canjear un evento
@app.route('/claim_ticket/<string:ticket_code>', methods=['POST'])
def claim_ticket(ticket_code):
    #primero busco el boleto en la base de datos
    cursor.execute("SELECT event_id, is_claimed FROM boletos WHERE ticket_code = %s", (ticket_code,))
    ticket = cursor.fetchone()

    if not ticket:
        return jsonify({"error": "Boleto no encontrado."}), 404

    event_id, is_claimed = ticket

    #aqui checo si el boleto ya fue canjeado
    if is_claimed:
        return jsonify({"error": "Este boleto ya ha sido canjeado."}), 400

    #busco el evento que corresponde
    cursor.execute("SELECT start_date, end_date FROM eventos WHERE id = %s", (event_id,))
    event = cursor.fetchone()

    if not event:
        return jsonify({"error": "Evento no encontrado."}), 404

    start_date, end_date = event

    current_date = datetime.now()
    if current_date < start_date or current_date > end_date:
        return jsonify({"error": "El boleto no puede ser canjeado fuera del rango de fechas del evento."}), 400
    
    claim_date = current_date
    query = "UPDATE boletos SET is_claimed = TRUE, claim_date = %s WHERE ticket_code = %s"
    values = (claim_date, ticket_code)

    try:
        cursor.execute(query, values)
        db.commit()
        return jsonify({"message": "Boleto canjeado exitosamente."}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

# Ruta para verificar estado de canje de un boleto
@app.route('/ticket_status/<string:ticket_code>', methods=['GET'])
def ticket_status(ticket_code):
    cursor.execute("SELECT is_claimed, claim_date FROM boletos WHERE ticket_code = %s", (ticket_code,))
    ticket = cursor.fetchone()
    if not ticket:
        return jsonify({"error": "Boleto no encontrado."}), 404
    is_claimed, claim_date = ticket
    return jsonify({
        "ticket_code": ticket_code,
        "is_claimed": is_claimed,
        "claim_date": claim_date
    })

# Ruta para ver detalles del evento
@app.route('/event_detail/<int:event_id>', methods=['GET'])
def event_detail(event_id):
    cursor.execute("SELECT name, start_date, end_date, total_tickets FROM eventos WHERE id = %s", (event_id,))
    event = cursor.fetchone()

    if not event:
        return jsonify({"error": "Evento no encontrado."}), 404

    name, start_date, end_date, total_tickets = event

    cursor.execute("SELECT COUNT(*) FROM boletos WHERE event_id = %s AND is_claimed = FALSE", (event_id,))
    sold_tickets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM boletos WHERE event_id = %s AND is_claimed = TRUE", (event_id,))
    tickets_claimed = cursor.fetchone()[0]

    tickets_available = total_tickets - sold_tickets

    return jsonify({
        "name": name,
        "start_date": start_date,
        "end_date": end_date,
        "total_tickets": total_tickets,
        "sold_tickets": sold_tickets,
        "tickets_claimed": tickets_claimed,
        "tickets_available": tickets_available
    })

if __name__ == '__main__':
    app.run(debug=True)
