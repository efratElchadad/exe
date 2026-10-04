#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>
#include <stdio.h>
#include "payload-config.h"

static int fail(const wchar_t *message) {
    MessageBoxW(NULL,message,L"AndroidCompiler",MB_OK|MB_ICONERROR);
    return 1;
}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE old,PWSTR args,int show) {
    wchar_t self[32768],local[32768],dest[32768],system[32768],ps[32768],command[32768],app[32768],cwd[32768];
    DWORD n=GetModuleFileNameW(NULL,self,32768);
    if(!n||n>=32768)return fail(L"Application path is too long.");
    n=GetEnvironmentVariableW(L"LOCALAPPDATA",local,32768);
    if(!n||n>=32768)return fail(L"Windows local application data folder is unavailable.");
    if(_snwprintf(dest,32768,L"%ls\\AndroidCompilerPortable\\" PACKAGE_ID,local)<0)return 1;
    GetSystemDirectoryW(system,32768);
    if(_snwprintf(ps,32768,L"%ls\\WindowsPowerShell\\v1.0\\powershell.exe",system)<0)return 1;
    SetEnvironmentVariableW(L"AC_PACKAGE_SELF",self);
    SetEnvironmentVariableW(L"AC_PACKAGE_DEST",dest);
    SetEnvironmentVariableW(L"AC_PACKAGE_SHA",PACKAGE_SHA);
    if(_snwprintf(command,32768,L"\"%ls\" -NoLogo -NoProfile -NonInteractive -EncodedCommand " EXTRACTION_COMMAND,ps)<0)return 1;
    HWND splash=CreateWindowExW(WS_EX_TOPMOST,L"STATIC",L"Preparing AndroidCompiler...\r\nFirst launch may take a few moments.",WS_OVERLAPPED|WS_CAPTION|WS_VISIBLE|SS_CENTER, CW_USEDEFAULT,CW_USEDEFAULT,460,110,NULL,NULL,instance,NULL);
    UpdateWindow(splash);
    STARTUPINFOW startup={0};startup.cb=sizeof(startup);PROCESS_INFORMATION process={0};
    if(!CreateProcessW(ps,command,NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,local,&startup,&process)) {
        DestroyWindow(splash);return fail(L"Windows PowerShell could not start. This package uses the standard Windows extraction components. No execution policy override is applied.");
    }
    CloseHandle(process.hThread);
    DWORD began=GetTickCount();
    while(WaitForSingleObject(process.hProcess,50)==WAIT_TIMEOUT) {
        MSG message;
        while(PeekMessageW(&message,NULL,0,0,PM_REMOVE)){TranslateMessage(&message);DispatchMessageW(&message);}
        if(GetTickCount()-began>180000){TerminateProcess(process.hProcess,1);break;}
    }
    DWORD exitcode=1;GetExitCodeProcess(process.hProcess,&exitcode);CloseHandle(process.hProcess);DestroyWindow(splash);
    SetEnvironmentVariableW(L"AC_PACKAGE_SELF",NULL);SetEnvironmentVariableW(L"AC_PACKAGE_DEST",NULL);SetEnvironmentVariableW(L"AC_PACKAGE_SHA",NULL);
    if(exitcode!=0)return fail(L"Could not prepare AndroidCompiler. Details: %LOCALAPPDATA%\\AndroidCompilerPortable\\extraction-error.log");
    if(_snwprintf(cwd,32768,L"%ls\\AndroidCompiler",dest)<0)return 1;
    if(_snwprintf(app,32768,L"%ls\\AndroidCompiler.exe",cwd)<0)return 1;
    if(_snwprintf(command,32768,L"\"%ls\"",app)<0)return 1;
    if(!CreateProcessW(app,command,NULL,NULL,FALSE,0,NULL,cwd,&startup,&process))return fail(L"The extracted application could not start.");
    CloseHandle(process.hThread);CloseHandle(process.hProcess);
    return 0;
}
