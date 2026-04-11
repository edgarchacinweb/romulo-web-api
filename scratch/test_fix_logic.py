def test_consolidation():
    # Mock data
    materias_rows = [
        ("id1", "Psicología"),
        ("id2", "Psicología"),
        ("id3", "Matemática")
    ]
    
    notas_dict = {
        ("id1", "lapso1"): 15,
        ("id2", "lapso2"): 18,
        ("id3", "lapso1"): 20
    }
    
    inasistencias_dict = {
        ("id1", "lapso1"): 2,
        ("id2", "lapso1"): 1,
        ("id3", "lapso1"): 0
    }
    
    lapsos = [
        {"id": "lapso1", "numero": 1, "visible": True},
        {"id": "lapso2", "numero": 2, "visible": True}
    ]

    # Logic copied from the fix
    reporte = []
    materias_agrupadas = {}
    for m_id, m_nombre in materias_rows:
        if m_nombre not in materias_agrupadas:
            materias_agrupadas[m_nombre] = []
        materias_agrupadas[m_nombre].append(m_id)

    for m_nombre, ids in materias_agrupadas.items():
        row_data = {"materia": m_nombre, "lapsos": []}
        total_inasistencias_materia = 0

        for l in lapsos:
            nota = None
            inasistencia_lapso = 0
            for current_id in ids:
                val_nota = notas_dict.get((current_id, l["id"]))
                if val_nota is not None:
                    nota = val_nota
                inasistencia_lapso += inasistencias_dict.get((current_id, l["id"]), 0)
            
            total_inasistencias_materia += inasistencia_lapso
            row_data["lapsos"].append({
                "numero": l["numero"],
                "nota": nota,
                "inasistencias": inasistencia_lapso
            })
        row_data["total_inasistencias"] = total_inasistencias_materia
        reporte.append(row_data)

    # Verification
    print(f"Reporte size: {len(reporte)} (Expected 2)")
    for r in reporte:
        print(f"Materia: {r['materia']}")
        for l in r['lapsos']:
            print(f"  Lapso {l['numero']}: Nota={l['nota']}, Inasistencias={l['inasistencias']}")
        print(f"  Total Inasistencias: {r['total_inasistencias']}")

if __name__ == "__main__":
    test_consolidation()
