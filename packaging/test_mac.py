import json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path
worker=Path(__file__).resolve().parents[1]/'androidcompiler/mac_worker.py'
def main():
    for engine in ('python','dotnet'):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with zipfile.ZipFile(root/'source.zip','w') as z:
                if engine=='python':z.writestr('main.py','from pathlib import Path\nPath("smoke-result.txt").write_text("OK")\n')
                else:
                    z.writestr('App.csproj','<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>')
                    z.writestr('Program.cs','System.IO.File.WriteAllText("smoke-result.txt", "OK");')
            (root/'build-config.json').write_text(json.dumps({'entry':'main.py' if engine=='python' else 'App.csproj','engine':engine,'kind':'Release','smoke':True}))
            subprocess.run([sys.executable,str(worker)],cwd=root,check=True)
            assert (root/'artifacts/Application.dmg').stat().st_size>1000
            print('REAL MAC '+engine+' BUILD, EXECUTION AND DMG PASSED',flush=True)

if __name__=='__main__':main()
