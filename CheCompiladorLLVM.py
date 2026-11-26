from pathlib import Path
import shutil
import subprocess

from llvmlite import binding


TRIPLE = "x86_64-pc-windows-msvc"


def generar_objeto(modulo_ir, ruta_objeto, opt=0):
    """Convierte el IR de llvmlite en un .obj COFF x64 (AOT, no JIT)."""

    # Hacen falta LAS DOS: sin native_asmprinter el codegen no tiene MCAsmInfo
    # y emit_object falla con "TargetMachine can't emit a file of this type".
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()

    target = binding.Target.from_triple(TRIPLE)

    # codemodel="default" es OBLIGATORIO en Windows. El default "jitdefault"
    # le agrega "-elf" al triple y emite un objeto ELF, inservible aca.
    target_machine = target.create_target_machine(opt=opt, codemodel="default")

    # Convertir el IR de llvmlite.ir a binding
    modulo = binding.parse_assembly(str(modulo_ir))

    # Configurar plataforma y layout
    modulo.triple = target_machine.triple
    modulo.data_layout = str(target_machine.target_data)

    # Verificar el modulo
    modulo.verify()

    # Generar codigo objeto
    objeto = target_machine.emit_object(modulo)

    # Chequeo de formato: los 2 primeros bytes de un COFF x64 son 64 86
    if objeto[:2].hex() != "6486":
        raise RuntimeError(
            "El objeto no es COFF x64 (magic %s). Triple: %s"
            % (objeto[:4].hex(), target_machine.triple)
        )

    # Guardar objeto (creando la carpeta si no existe)
    ruta_objeto = Path(ruta_objeto)
    ruta_objeto.parent.mkdir(parents=True, exist_ok=True)
    ruta_objeto.write_bytes(objeto)

    return ruta_objeto


def buscar_linker():
    """Devuelve una funcion que arma el comando de link, o None si no hay linker."""
    #TODO deberiamos usar siempre clang y ponerlo dentro de la carpeta del proyecto o como requisito en el instalador
    clang = shutil.which("clang")
    if clang:
        return lambda obj, exe: [clang, obj, "-o", exe]

    gcc = shutil.which("gcc")
    if gcc:
        return lambda obj, exe: [gcc, obj, "-o", exe]

    zig = shutil.which("zig")
    if zig:
        return lambda obj, exe: [zig, "cc", obj, "-o", exe]

    # cl solo aparece en el PATH dentro del "x64 Native Tools Command Prompt"
    cl = shutil.which("cl")
    if cl:
        return lambda obj, exe: [cl, obj, "/Fe:" + exe]

    return None


def linkear(ruta_objeto, ruta_exe, linker=None):
    armar_comando = linker or buscar_linker()

    if armar_comando is None:
        raise RuntimeError(
            "No hay linker instalado (clang / gcc / zig / cl).\n"
            "El objeto quedo generado en %s; linkealo a mano con:\n"
            "  clang %s -o %s" % (ruta_objeto, ruta_objeto, ruta_exe)
        )

    subprocess.run(armar_comando(str(ruta_objeto), str(ruta_exe)), check=True)


def compilar(modulo_ir, ruta_exe, linker=None, opt=0):
    ruta_exe = Path(ruta_exe)
    ruta_objeto = generar_objeto(modulo_ir, ruta_exe.with_suffix(".obj"), opt=opt)
    linkear(ruta_objeto, ruta_exe, linker=linker)
    return ruta_exe