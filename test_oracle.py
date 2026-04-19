from knowledge_oracle import query_oracle

question = "cómo funciona el protocolo de inteligencia híbrida y qué modelos usa"
results = query_oracle(question, top_k=3)

print("=== RESPUESTA DEL ORÁCULO VECTORIAL ===")
for i, r in enumerate(results, 1):
    print(f"\n[{i}] FUENTE: {r['file']}")
    print(f"DISTANCIA: {r['distance']:.4f}")
    print(f"CONTENIDO: {r['text'][:500]}...")
    print("-" * 50)
