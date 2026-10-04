"""Real managed-toolchain builds and execution. Used only by Windows CI."""
import os,subprocess,tempfile
from pathlib import Path
from androidcompiler.project import Workspace
from androidcompiler.desktop import analyze_desktop,DesktopBuilder
from androidcompiler.runtime import Runner,CommandFailed

def main():
    assert os.name=='nt'
    with tempfile.TemporaryDirectory() as temp:
        base=Path(temp);runner=Runner(print,print)
        for engine in ('python','dotnet'):
            src=base/engine;src.mkdir()
            if engine=='python':(src/'main.py').write_text('print("REAL_EXE_OK")')
            else:
                (src/'App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>')
                (src/'Program.cs').write_text('System.Console.WriteLine("REAL_EXE_OK");')
            w=Workspace(base/'work')
            try:
                project=w.import_project(src,lambda s,w:analyze_desktop(s,w,engine))
                results=DesktopBuilder(base/'app',runner).build(project,project.modules[0],output_root=base/'chosen output')
                exe=Path(results[0]['path']);assert exe.is_relative_to(base/'chosen output')
                output=subprocess.check_output([str(exe)],text=True,timeout=60)
                assert 'REAL_EXE_OK' in output
                print('REAL '+engine+' EXE EXECUTION PASSED')
                # Invalid code must fail and must not leave a successful output directory.
                if engine=='python':project.modules[0].directory.write_text('def broken(:')
                else:(project.root/'Program.cs').write_text('this is invalid C#;')
                before=set((base/'chosen output').iterdir())
                try:DesktopBuilder(base/'app',runner).build(project,project.modules[0],output_root=base/'chosen output')
                except CommandFailed:pass
                else:raise AssertionError('Invalid source unexpectedly built')
                assert set((base/'chosen output').iterdir())==before
                print('REAL '+engine+' FAILURE HANDLING PASSED')
            finally:w.close()
if __name__=='__main__':main()
