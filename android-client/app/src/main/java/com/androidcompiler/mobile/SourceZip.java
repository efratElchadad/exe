package com.androidcompiler.mobile;
import java.io.*;
import java.util.*;
import java.util.zip.*;
final class SourceZip {
 static List<String> inspect(File file,String engine) throws IOException {
  List<String> entries=new ArrayList<>();Set<String> seen=new HashSet<>();long total=0;int count=0;
  try(ZipFile z=new ZipFile(file)){
   Enumeration<? extends ZipEntry> it=z.entries();
   while(it.hasMoreElements()){
    ZipEntry e=it.nextElement();String n=e.getName();safe(n);
    if(!seen.add(n.toLowerCase(Locale.ROOT)))throw new IOException("שמות קבצים כפולים ב־ZIP");
    if(++count>30000 || e.getSize()<0 || (total+=e.getSize())>1024L*1024*1024)throw new IOException("הפרויקט גדול מדי");
    if(e.isDirectory())continue;
    if((engine.equals("android")&&(n.endsWith("build.gradle")||n.endsWith("build.gradle.kts"))) || (engine.equals("python")&&(n.endsWith(".py")||n.endsWith(".spec"))) || (engine.equals("dotnet")&&n.endsWith(".csproj")))entries.add(n);
   }
  }
  entries.sort(Comparator.comparingInt(n->n.endsWith("main.py")?0:n.endsWith("app/build.gradle.kts")||n.endsWith("app/build.gradle")?0:1));
  if(entries.isEmpty())throw new IOException("לא נמצא קובץ כניסה מתאים לסוג הפרויקט שנבחר");return entries;
 }
 static void safe(String n)throws IOException{
  if(n.startsWith("/")||n.contains("\\")||n.contains(":"))throw new IOException("נתיב ZIP לא תקין");
  for(String p:n.split("/"))if(p.equals("..")||p.equals("."))throw new IOException("נתיב ZIP לא תקין");
 }
}
