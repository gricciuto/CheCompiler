from llvmlite import binding
from pathlib import Path
import subprocess


def generar_objeto(modulo_ir, ruta_objeto, opt=0):

    # Inicializar LLVM
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()

    triple = "x86_64-pc-windows-msvc"

    target = binding.Target.from_triple(triple)

    target_machine = target.create_target_machine(
        opt=opt
    )

    # Convertir el IR de llvmlite.ir a binding
    modulo = binding.parse_assembly(str(modulo_ir))

    # Configurar plataforma y layout
    modulo.triple = target_machine.triple
    modulo.data_layout = str(target_machine.target_data)

    # Verificar el módulo
    modulo.verify()

    # Generar código objeto
    objeto = target_machine.emit_object(modulo)

    # Guardar objeto
    Path(ruta_objeto).write_bytes(objeto)
    objeto = target_machine.emit_object(modulo)

    print("Triple de LLVM:", binding.get_default_triple())
    print("Triple del target:", target_machine.triple)
    print("Primeros 16 bytes:", objeto[:16].hex(" "))

    Path(ruta_objeto).write_bytes(objeto)
    return target_machine


def linkear(ruta_objeto, ruta_exe, clang="clang"):

    subprocess.run(
        [
            clang,
            str(ruta_objeto),
            "-o",
            str(ruta_exe)
        ],
        check=True
    )


def compilar(modulo_ir, ruta_exe, clang="clang", opt=0):

    ruta_exe = Path(ruta_exe)
    ruta_objeto = ruta_exe.with_suffix(".obj")

    # Generar objeto
    generar_objeto(
        modulo_ir,
        ruta_objeto,
        opt=opt
    )

    # Linkear
    linkear(
        ruta_objeto,
        ruta_exe,
        clang=clang
    )

    return ruta_exe