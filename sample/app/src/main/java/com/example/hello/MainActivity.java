package com.example.hello;
import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
public class MainActivity extends Activity {
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    TextView text = new TextView(this);
    text.setText("Built with AndroidCompiler"); text.setTextSize(24); text.setGravity(17);
    setContentView(text);
  }
}
