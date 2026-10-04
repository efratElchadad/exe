#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>
#include <stdio.h>

int WINAPI wWinMain(HINSTANCE h, HINSTANCE previous, PWSTR extra, int show) {
    wchar_t root[32768], interpreter[32768], command[32768];
    DWORD n = GetModuleFileNameW(NULL, root, 32768);
    if (!n || n >= 32768) return 2;
    wchar_t *slash = wcsrchr(root, L'\\');
    if (!slash) return 2;
    *slash = 0;
    if (_snwprintf(interpreter, 32768, L"%ls\\runtime\\pythonw.exe", root) < 0) return 2;
    if (GetFileAttributesW(interpreter) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(NULL, L"Extract the entire ZIP first. Keep AndroidCompiler.exe together with its app and runtime folders.", L"AndroidCompiler", MB_OK | MB_ICONERROR);
        return 3;
    }
    if (_snwprintf(command, 32768, L"\"%ls\" \"%ls\\app\\bootstrap.py\" %ls", interpreter, root, extra) < 0) return 2;
    STARTUPINFOW si = {0}; si.cb = sizeof(si);
    PROCESS_INFORMATION pi = {0};
    if (!CreateProcessW(interpreter, command, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, root, &si, &pi)) {
        MessageBoxW(NULL, L"Could not start the bundled runtime. See README-HE.md or check security software quarantine.", L"AndroidCompiler", MB_OK | MB_ICONERROR);
        return 4;
    }
    CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD code = 1; GetExitCodeProcess(pi.hProcess, &code); CloseHandle(pi.hProcess);
    return (int)code;
}
