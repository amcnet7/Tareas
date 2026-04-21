import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def buscar_rfc_en_xml(ruta_carpeta, rfc):
    """
    Busca un RFC en archivos XML de una carpeta y sus subcarpetas.
    Muestra el nombre del archivo y el valor de ValorUnitario si lo encuentra.
    """
    
    # Validar que la ruta existe
    if not os.path.isdir(ruta_carpeta):
        print(f"❌ Error: La ruta '{ruta_carpeta}' no existe o no es una carpeta.")
        return
    
    print(f"\n🔍 Buscando RFC: {rfc}")
    print(f"📁 En la carpeta: {ruta_carpeta}")
    print("-" * 80)
    
    archivos_encontrados = []
    
    # Buscar archivos XML recursivamente
    for raiz, carpetas, archivos in os.walk(ruta_carpeta):
        for archivo in archivos:
            if archivo.lower().endswith('.xml'):
                ruta_archivo = os.path.join(raiz, archivo)
                
                try:
                    # Leer el contenido del archivo como texto
                    with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                        contenido = f.read()
                    
                    # Buscar si el RFC está en el archivo
                    if rfc.upper() in contenido.upper():
                        # Buscar el valor de ValorUnitario
                        patron = r'ValorUnitario\s*=\s*"([^"]*)"'
                        coincidencias = re.findall(patron, contenido)
                        
                        resultado = {
                            'archivo': archivo,
                            'ruta_completa': ruta_archivo,
                            'valores': coincidencias
                        }
                        archivos_encontrados.append(resultado)
                
                except Exception as e:
                    print(f"⚠️ Error al procesar {archivo}: {str(e)}")
    
    # Mostrar resultados
    if archivos_encontrados:
        print(f"✅ Se encontraron {len(archivos_encontrados)} archivo(s) con el RFC '{rfc}':\n")
        
        for idx, resultado in enumerate(archivos_encontrados, 1):
            print(f"{idx}. Archivo: {resultado['archivo']}")
            print(f"   Ruta: {resultado['ruta_completa']}")
            
            if resultado['valores']:
                print(f"   Valores de ValorUnitario encontrados:")
                for i, valor in enumerate(resultado['valores'], 1):
                    print(f"      - {i}: {valor}")
            else:
                print(f"   ⚠️ RFC encontrado pero sin valores de ValorUnitario")
            
            print()
    else:
        print(f"❌ No se encontró el RFC '{rfc}' en ningún archivo XML.")

def main():
    """Función principal."""
    print("=" * 80)
    print("BUSCADOR DE RFC EN ARCHIVOS XML")
    print("=" * 80)
    
    # Solicitar ruta de la carpeta
    ruta_carpeta = input("\n📁 Ingresa la ruta de la carpeta: ").strip()
    ruta_carpeta = ruta_carpeta.strip('"')  # Eliminar comillas si las hay
    
    # Solicitar RFC
    rfc = input("🔐 Ingresa el RFC a buscar: ").strip()
    
    if not rfc:
        print("❌ Error: Debes ingresar un RFC.")
        return
    
    # Ejecutar búsqueda
    buscar_rfc_en_xml(ruta_carpeta, rfc)

if __name__ == "__main__":
    main()
