package com.androidcompiler.mobile;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;import org.junit.runner.RunWith;
import java.io.*;import java.util.zip.*;import java.util.*;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class ClientTest {
 File zip(String... names)throws Exception{
  File f=File.createTempFile("source",".zip",InstrumentationRegistry.getInstrumentation().getTargetContext().getCacheDir());
  try(ZipOutputStream z=new ZipOutputStream(new FileOutputStream(f))){for(String n:names){z.putNextEntry(new ZipEntry(n));z.write("sample".getBytes());z.closeEntry();}}return f;
 }
 @Test public void opensRealScreenAndGuide()throws Exception{
  try(ActivityScenario<MainActivity> scenario=ActivityScenario.launch(MainActivity.class)){
   scenario.onActivity(a->{assertTrue(a.build.isShown());assertEquals(5,a.target.getCount());assertFalse(BuildService.running);assertEquals("android",a.engine());a.target.setSelection(3);assertEquals("mac",a.platform());assertEquals("python",a.engine());assertNotNull(a.getDrawable(R.drawable.app_logo));});
  }
 }
 @Test public void scansAndroidAndDesktopSources()throws Exception{
  File f=zip("Project/build.gradle.kts","Project/app/build.gradle.kts","Project/main.py","Project/Hello.csproj");
  try{assertEquals("Project/app/build.gradle.kts",SourceZip.inspect(f,"android").get(0));assertEquals(Arrays.asList("Project/main.py"),SourceZip.inspect(f,"python"));assertEquals(1,SourceZip.inspect(f,"dotnet").size());}finally{f.delete();}
 }
 @Test public void rejectsTraversalAndAmbiguousNames()throws Exception{
  for(String[] names:new String[][]{{"../main.py"},{"C:/main.py"},{"main.py","MAIN.py"},{"folder\\main.py"}}){File f=zip(names);try{SourceZip.inspect(f,"python");fail("Unsafe ZIP accepted");}catch(IOException expected){}finally{f.delete();}}
 }
 @Test public void showsValidationWithoutStartingService()throws Exception{
  try(ActivityScenario<MainActivity> s=ActivityScenario.launch(MainActivity.class)){s.onActivity(a->{a.ready=false;a.build.performClick();assertFalse(BuildService.running);});}
 }
 @Test public void bundledEngineAndWorkflowArePresent()throws Exception{
  android.content.Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
  try(InputStream in=c.getAssets().open("workflow.yml")){String workflow=CloudApi.read(in);assertTrue(workflow.contains("RUNNER"));assertTrue(workflow.contains("cloud_job.py"));assertFalse(workflow.contains("Bearer"));}
  Set<String> names=new HashSet<>();try(ZipInputStream z=new ZipInputStream(c.getAssets().open("cloud-engine.zip"))){ZipEntry e;while((e=z.getNextEntry())!=null)names.add(e.getName());}assertTrue(names.contains("androidcompiler/cloud_job.py"));assertTrue(names.contains("androidcompiler/build.py"));
 }
 @Test public void importsActualZipThroughActivityResult()throws Exception{
  File f=zip("Project/app/build.gradle.kts");java.util.concurrent.atomic.AtomicBoolean ready=new java.util.concurrent.atomic.AtomicBoolean(false);
  try(ActivityScenario<MainActivity> s=ActivityScenario.launch(MainActivity.class)){
   s.onActivity(a->{a.target.setSelection(0);a.onActivityResult(1,android.app.Activity.RESULT_OK,new android.content.Intent().setData(android.net.Uri.fromFile(f)));});
   long end=System.currentTimeMillis()+10000;
   do{Thread.sleep(100);s.onActivity(a->ready.set(a.ready));}while(!ready.get()&&System.currentTimeMillis()<end);
   assertTrue("ZIP import did not complete",ready.get());s.onActivity(a->{assertEquals("Project/app/build.gradle.kts",a.entry.getSelectedItem());a.showLog();});
  }finally{f.delete();}
 }
}
