from pathlib import Path
import pytest
from androidcompiler.desktop import analyze_desktop,DesktopBuilder
from androidcompiler.project import Workspace,ProjectError

def test_python_import_entry_selection(tmp_path):
    src=tmp_path/'src';src.mkdir();(src/'main.py').write_text('print(1)');(src/'helper.py').write_text('')
    w=Workspace(tmp_path/'work')
    try:
        p=w.import_project(src,lambda s,w:analyze_desktop(s,w,'python'))
        assert p.engine=='python' and p.modules[0].name=='main.py'
        assert p.root!=src
    finally:w.close()

def test_dotnet_analysis_and_library_rejection(tmp_path):
    p=tmp_path/'app.csproj';p.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net8.0</TargetFramework><OutputType>Exe</OutputType></PropertyGroup></Project>')
    project=analyze_desktop(tmp_path,tmp_path,'dotnet');assert project.modules[0].compile_sdk=='net8.0'
    p.write_text(p.read_text().replace('>Exe<','>Library<'))
    with pytest.raises(ProjectError):analyze_desktop(tmp_path,tmp_path,'dotnet')
