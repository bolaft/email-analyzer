package common.util;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintWriter;

public class IO {
	
	/**
	 * Prints a string to the file system
	 * @param text
	 * @param filename
	 * @param append
	 */
	public static void write(String text, String filename, Boolean append) {
		PrintWriter out = null;
		
		try {
			out = new PrintWriter(new FileOutputStream(new File(filename), append));
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
		
		out.println(text);
		out.close();
	}
	
	/**
	 * http://stackoverflow.com/questions/326390/how-to-create-a-java-string-from-the-contents-of-a-file
	 * Alternative exists: slower but less memory consuming
	 * @throws IOException 
	 */
	public  static String read(String path) throws IOException{
		FileInputStream stream = null;
		
		File f = new File(path);
		stream = new FileInputStream(f);
		stream.close();

		BufferedReader reader = null;
		
		reader = new BufferedReader( new FileReader (path));

		StringBuilder builder = new StringBuilder();
		String aux = "";
		
		while ((aux = reader.readLine()) != null) {
			builder.append(aux);builder.append("\n");
		}
		
		reader.close();

		return builder.toString();
	}
}
