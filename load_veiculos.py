from app import app
from models import db, Veiculo

# Frota definida manualmente com base na imagem
frota_par = [1442, 1444, 1446, 1448, 1450, 1452, 1454, 1456, 1458, 1460, 1462, 1464, 1466, 1468, 1470, 1472, 1474, 1476]
frota_impar = [1443, 1445, 1447, 1449, 1451, 1453, 1455, 1457, 1459, 1461, 1463, 1465, 1467, 1469, 1471, 1473, 1475, 1477]

with app.app_context():
    for numero in frota_par:
        if not Veiculo.query.filter_by(numero_frota=numero).first():
            db.session.add(Veiculo(numero_frota=numero, tipo_frota='PAR'))

    for numero in frota_impar:
        if not Veiculo.query.filter_by(numero_frota=numero).first():
            db.session.add(Veiculo(numero_frota=numero, tipo_frota='IMPAR'))
            db.session.commit() 

    db.session.commit()
    print("Frota PAR e IMPAR cadastradas com sucesso!")
