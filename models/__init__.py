"""MODELO (la «M» del MVC).

Aquí viven las clases que representan los datos de EDUDEBUG y que son las ÚNICAS que hablan con las bases:

  SQLite  (relacional) : Usuario, Curso, Modulo, TestDiagnostico, PreguntaTest, EnvioCodigo,
                         ErrorDetectado, Recomendacion
  MongoDB (documentos) : Actividad, Comentario

Ningún controlador ni servicio escribe SQL: piden lo que necesitan a estas clases.
Las clases son datos y acceso a datos; las reglas de negocio están en services/.
"""
