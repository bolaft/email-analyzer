package common.util;

import java.text.SimpleDateFormat;
import java.util.Date;

public class Out {

	public final static int ERROR_LEVEL = 0;
	public final static int INFO_LEVEL = 1;
	public final static int WARN_LEVEL = 2;
	public final static int DEBUG_LEVEL = 3;
	
	public static int LEVEL = 1;
	
	public static String dirpath = "log/";
	
	public static boolean SAVE_TO_FILE = true;
	
	public static void print(String text) {
		print(text, DEBUG_LEVEL);
	}
	
	public static void print(String text, int level) {
		StackTraceElement[] trace = Thread.currentThread().getStackTrace();
		StackTraceElement called = null;
		String className = null;
		
		if (trace[2].getClassName().equals(Out.class.getName())) {
			called = trace[3];
		} else {
			called = trace[2];
		}
		
		className = called.getClassName().substring(called.getClassName().lastIndexOf(".") + 1);

		Boolean write = false;
		if (level < DEBUG_LEVEL) write = true;
		
		String canal = "out";
		if (level == ERROR_LEVEL || level == WARN_LEVEL) canal = "err";
		
		Date currentDate = new Date();
		
		String date = new SimpleDateFormat("yyyy-MM-dd").format(currentDate);
		String time = new SimpleDateFormat("HH:mm:ss").format(currentDate);
		
		String message = time + " - " + className + " - " + text;
		
		if (write && SAVE_TO_FILE) IO.write(message, dirpath + date + ".log", true);
		
		if (level > LEVEL) return;
		
		if (canal.equals("err")) {
			System.err.println(message);
		} else {
			System.out.println(message);
		}
	}
}
