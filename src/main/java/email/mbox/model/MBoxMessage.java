package email.mbox.model;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;

import javax.mail.MessagingException;
import javax.mail.internet.MimeUtility;

import org.apache.commons.io.IOUtils;

import com.auxilii.msgparser.Message;
import com.sun.mail.util.DecodingException;

import common.util.Out;
import factory.parser.MBoxParser;
import fr.univnantes.lina.javautil.IOUtilities;

/**
 * @author hernandez
 */
public class MBoxMessage {

	private Date date;
	private String toName;
	private String toEmail;

	private String fromEmail;
	private String fromName;

	private String messageId;
	private String subject;
	private String inReplyTo;
	private String text;	

	public MBoxMessage(String mboxMessage) {
		MBoxParser mboxParser = new MBoxParser();
		Message message = null;
		
		try {
			message  = mboxParser.parse(mboxMessage);
		} catch (Exception e) {
			e.printStackTrace();
		}

		setText(extractText(mboxMessage));
		setDate(message.getDate());
		setToName(message.getToName());
		setToEmail(message.getToEmail());
		setFromEmail(message.getFromEmail());
		setFromName(message.getFromName());
		setSubject(message.getSubject());
		setInReplyTo(getInReplyTo(message));
		setMessageId(message.getMessageId());
	}

	/**
	 * @param message
	 * @return
	 */
	public static String getInReplyTo(Message message) {
		String inReplyTo = "";
		
		for (String p : message.getProperties()) {
			if (p.equalsIgnoreCase("In-Reply-To-Email")) inReplyTo = (String) message.getProperty(p);
		}
		
		return inReplyTo;
	}

	/**
	 * @return the date
	 */
	public Date getDate() {
		return date;
	}

	/**
	 * @param date2 the date to set
	 */
	public void setDate(Date date2) {
		this.date = date2;
	}

	/**
	 * @return the to
	 */
	public String getToName() {
		return toName;
	}

	/**
	 * @param to the to to set
	 */
	public void setToName(String to) {
		this.toName = to;
	}

	/**
	 * @return the to
	 */
	public String getToEmail() {
		return toEmail;
	}

	/**
	 * @param to the to to set
	 */
	public void setToEmail(String to) {
		this.toEmail = to;
	}

	/**
	 * @return the from
	 */
	public String getFromName() {
		return fromName;
	}

	/**
	 * @param from the from to set
	 */
	public void setFromName(String from) {
		this.fromName = from;
	}

	/**
	 * @return the from
	 */
	public String getFromEmail() {
		return fromEmail;
	}

	/**
	 * @param from the from to set
	 */
	public void setFromEmail(String from) {
		this.fromEmail = from;
	}

	/**
	 * @return the messageId
	 */
	public String getMessageId() {
		return messageId;
	}

	/**
	 * @param messageId the messageId to set
	 */
	public void setMessageId(String messageId) {
		this.messageId = stripMessageId(messageId);
	}

	/**
	 * @return the subject
	 */
	public String getSubject() {
		return subject;
	}

	/**
	 * @param subject the subject to set
	 */
	public void setSubject(String subject) {
		this.subject = subject;
	}

	/**
	 * @return the inReplyTo
	 */
	public String getInReplyTo() {
		return inReplyTo;
	}

	/**
	 * @param inReplyTo the inReplyTo to set
	 */
	public void setInReplyTo(String inReplyTo) {
		this.inReplyTo = inReplyTo;
	}

	/**
	 * @return the text
	 */
	public String getText() {
		return text;
	}

	/**
	 * @param text the text to set
	 */
	public void setText(String text) {
		this.text = text;
	}

	/**
	 * @param text
	 * @param start
	 * @return
	 */
	private static int charsetStart(String text, int start) {
		//	int wss = text.indexOf(" "+charsetStartTag,start);		
		//	int tabs = text.indexOf("\t"+charsetStartTag,start);
		//	int colons = text.indexOf(";"+charsetStartTag,start);
		String charsetStartTag = "charset=";
		return text.indexOf(charsetStartTag,start);		
	}

	/**
	 * Content-Type: text/plain; charset=ISO-8859-1
	 * Content-Type: text/plain; charset=ISO-8859-1; format=flowed
	 * Content-Type: text/plain; charset="UTF-8"
	 * @param text
	 * @param start
	 * @return
	 */
	private static int charsetEnd(String text, int start) {
		int lineSeparator = text.indexOf(System.getProperty("line.separator"),start+contentTypeLength());
		int semiColon = text.indexOf(";",start+contentTypeLength());
		int ws = text.indexOf(" ",start+contentTypeLength());
		int end = lineSeparator;
		
		if (semiColon != -1) end = (semiColon < end ? semiColon : end);
		if (ws != -1) end = (ws < end ? ws : end);

		return end;
	}

	/**
	 * @param text
	 * @param start 
	 * @param end
	 */
	private static String getCharset(String text, int start, int end) {
		String charsetStartTag = "charset=";
		String value = text.substring(start+charsetStartTag.length(),end ).trim();
		
		if (value.startsWith("\"")) value = value.substring(1);

		if (value.endsWith("\"")) value = value.substring(0, value.length()-1);

		return value;
	}

	private static int contentTransfertEncodingLength() {
		return "Content-Transfer-Encoding: ".length(); //"Content-transfer-encoding: "
	}

	/**
	 * @param text
	 * @param start
	 * @return
	 */
	private static int contentTransfertEncodingStart(String text, int start) {
		int contentTransfertEncodingStart = text.indexOf("Content-Transfer-Encoding: ",start);

		if (contentTransfertEncodingStart == -1) contentTransfertEncodingStart = text.indexOf("Content-transfer-encoding: ",start);

		return contentTransfertEncodingStart;		
	}

	/**
	 * Content-Type: text/plain; charset=ISO-8859-1
	 * Content-Type: text/plain; charset=ISO-8859-1; format=flowed
	 * Content-Type: text/plain; charset="UTF-8"
	 * @param text
	 * @param start
	 * @return
	 */
	private static int contentTransfertEncodingEnd(String text, int start) {
		int lineSeparator = text.indexOf(System.getProperty("line.separator"),start+contentTransfertEncodingLength());
		int semiColon = text.indexOf(";",start+contentTransfertEncodingLength());
		int ws = text.indexOf(" ",start+contentTransfertEncodingLength());
		int end = lineSeparator;
		
		if (semiColon != -1) end = (semiColon < end ? semiColon : end);
		if (ws != -1) end = (ws < end ? ws : end);

		return end;
	}

	/**
	 * @param text
	 * @param start 
	 * @param end
	 */
	private static String getContentTransfertEncoding(String text, int start, int end) {
		return text.substring(start+contentTransfertEncodingLength(),end ).trim();
	}

	private static int contentTypeLength() {
		return "Content-Type:".length(); // which is the same than "Content-type:" 
	}
	
	/**
	 * @param text
	 * @param start
	 * @return
	 */
	private static int contentTypeStart(String text, int start) {
		int contentTypeStart = text.indexOf("Content-Type:",start);
		if (contentTypeStart == -1 )  text.indexOf("Content-type:",start);
		
		return contentTypeStart;		
	}

	/**
	 * @param text
	 * @param start
	 * @return
	 */
	private static int contentTypeEnd(String text, int start) {
		String contentTypeEndTag = ";";
		
		int end = text.indexOf(contentTypeEndTag,start+contentTypeLength());
		if (end == -1) end = text.indexOf(System.getProperty("line.separator"),start+contentTypeLength());
		
		return end;
	}

	/**
	 * @param text
	 * @param start 
	 * @param end
	 */
	private static String getContentType(String text, int start, int end) {
		return text.substring(start+contentTypeLength(),end ).trim();
	}

	/**
	 * @param text
	 * @param start
	 */
	private static int boundaryStart(String text, int start) {
		String boundaryStartTag = "boundary=";
		return text.indexOf(boundaryStartTag, start);
	}

	/**
	 * @param text
	 * @param start
	 */
	private static int boundaryEnd(String text, int start) {
		String boundaryStartTag = "boundary=";
		String boundaryEndTag = System.getProperty("line.separator");
		int end = text.indexOf(boundaryEndTag,start+boundaryStartTag.length());
		// Bug delimiting tbe boundary less message_1914378251186835958 Message-ID: <20130710195134.31b28da3@Jupiter>
		// Content-Type: multipart/signed; micalg=PGP-SHA1;
		// boundary="Sig_/V1GYfSJxhnvOStFXH=C790J"; protocol="application/pgp-signature"
		int ws = text.indexOf(" ",start+boundaryStartTag.length());
		
		return ws < end ? ws : end;
	}

	/**
	 * @param text
	 * @param start
	 * @param end
	 */
	private static String getBoundaryValue(String text, int start, int end) {
		// int boundaryEnd =text.indexOf(endTag,boundaryStart+startTag.length());
		// String boundary = text.substring(boundaryStart+startTag.length(), boundaryEnd).trim();
		String boundaryStartTag = "boundary=";
		String boundary = text.substring(start+boundaryStartTag.length(), end).trim();

		// bug 
		if (boundary.startsWith("\"") && boundary.endsWith("\";")) {
			boundary = boundary.substring(1, boundary.length()-2);
		} else if (boundary.startsWith("\"") && boundary.endsWith("\"")) {
			boundary = boundary.substring(1, boundary.length()-1);
		}
		// bug  <20060915154514.6992ccfc@localhost>
		else if (boundary.endsWith(";")) {
			boundary = boundary.substring(0, boundary.length()-1);
		}
		
		return boundary;
	}

	/**
	 * http://docs.oracle.com/javaee/6/api/javax/mail/internet/MimeUtility.html
	 * 
	 * @param text
	 * @param transferEncoding All the encodings defined in RFC 2045
	 * are supported here. They include "base64", "quoted-printable",
	 * "7bit", "8bit", and "binary". In addition, "uuencode" is also
	 * supported. 
	 * @param characterEncoding  "iso-8859-1"
	 * @return
	 * @throws IOException
	 */
	private static String contentTransferDecode(String text, String transferEncoding, String characterEncoding) {
		try {
			InputStream decodedIn = MimeUtility.decode(new ByteArrayInputStream(text.getBytes()), transferEncoding);

			StringWriter writer = new StringWriter();
			IOUtils.copy(decodedIn, writer,characterEncoding);
			text = writer.toString();
		} catch (UnsupportedEncodingException e) {
			Out.print("UnsupportedEncodingException raised with: " + transferEncoding + " / " + characterEncoding);
		} catch (DecodingException e) {
			Out.print("DecodingException raised with: " + transferEncoding + " / " + characterEncoding);
		} catch (MessagingException | IOException e) {
			e.printStackTrace();
		}
		
		return text;
	}

	/**
	 * in case of multipart type mime get the the text plain part if exists
	 * 
	 *	//Content-Type: multipart/alternative; boundary=Apple-Mail-12-530324206
	 *	//        boundary="------------060302040704070400040908"
	 *	//Content-Type: multipart/mixed; boundary="===============0697619449=="
	 *	//        micalg=pgp-sha1; boundary="Apple-Mail-13-530324224"
	 *	//		Content-Type: multipart/signed; boundary=Sig_qQ8g91I2LUinpKtzesqUe+f;
	 *	// text/plain
	 *	//
	 *	// get the next contextType value
	 *	// while contentType != "plain/text" do
	 *	// 		if multipart 
	 *	// 			get boundary value
	 *	// 			get the next boundary position
	 *	//			get the next contextType value from this position
	 *	//		else if != multipart and (multipart is true) // i.e. boundary value != null
	 *	//			get the next boundary position
	 *	//			get the next contextType value from this position
	 *	//			else unknown case
	 *	// if (multipart is true) 
	 *	// messagePlainTextStart = current boundaryPosition (minus some parasite lines)
	 *	// messagePlainTextStart = get the next boundary position (last line.separator)
	 * 
	 * @param emailMessage
	 * 
	 * @return
	 */
	private static String extractText(String emailMessage) {
		String charset = getCharset(emailMessage);

		String contentTransfertEncoding = getContentTransfertEncoding(emailMessage);

		if (!charset.toLowerCase().startsWith("iso") 
				&& !charset.toLowerCase().startsWith("utf")  
				&& !charset.toLowerCase().startsWith("us-ascii")  
				&& !charset.toLowerCase().startsWith("windows")) {
			Out.print("initial - contentTransfertEncoding " + contentTransfertEncoding + " ; charset " + charset + " ; header " + emailMessage.substring(0, emailMessage.length() < 160 ? emailMessage.length() : 160) , Out.WARN_LEVEL);
		}

		int contentTypetagStart = contentTypeStart(emailMessage, 0);
		int tagEnd = -1 ;

		String contentType = "";
		String boundaryValue = "";
		Boolean isMultiPart = false;
		
		int nextBoundaryStart = 0;

		// bug less message_5756816445682821472 <dlqrmk$tm9$1@sea.gmane.org> no ContentType
		if (contentTypetagStart != -1) {
			tagEnd = contentTypeEnd(emailMessage, contentTypetagStart);
			contentType = getContentType(emailMessage, contentTypetagStart, tagEnd);
			// bug: <47934A83.4060809@yahoo.fr> only one Content-Type: text/html; 

			Set<Integer> positionAlreadyVisited = new HashSet<Integer>();  

			if (contentType.toLowerCase().startsWith("multipart"))
				// bug <4388CE49.000010.00520@FREDRVMWARE> Content-Type: Text/Plain; (in uppercase)
				while (!contentType.toLowerCase().startsWith("text/plain")) {
					// bug Message-Id: <200412302317.27496.joeltarlao@neuf.fr>  Content-Type: Multipart/Mixed; (in uppercase)

					if (contentType.toLowerCase().startsWith("multipart")) {
						contentTypetagStart = boundaryStart(emailMessage, tagEnd);
						tagEnd =  boundaryEnd(emailMessage, contentTypetagStart);
						boundaryValue = getBoundaryValue(emailMessage, contentTypetagStart,  tagEnd);

						nextBoundaryStart = emailMessage.indexOf(System.getProperty("line.separator"), emailMessage.indexOf(boundaryValue, tagEnd));

						contentTypetagStart = contentTypeStart(emailMessage, nextBoundaryStart);
						tagEnd = contentTypeEnd(emailMessage, contentTypetagStart);

						contentType = getContentType(emailMessage, contentTypetagStart, tagEnd);
						isMultiPart = true;
					} else { 
						// searching for the part which is text/plain
						if (isMultiPart) {
							nextBoundaryStart = emailMessage.indexOf(System.getProperty("line.separator"), emailMessage.indexOf(boundaryValue, tagEnd));

							contentTypetagStart = contentTypeStart(emailMessage, nextBoundaryStart);
							tagEnd = contentTypeEnd(emailMessage, contentTypetagStart);

							contentType = getContentType(emailMessage, contentTypetagStart, tagEnd);
						} else {
							Out.print("contentType " + contentType + " boundary " + boundaryValue + " position " + tagEnd, Out.WARN_LEVEL);
						}
					}
					
					// Hack to avoid loop
					// May mask actual problems
					// in that case it will works with the whole message body
					if (positionAlreadyVisited.contains(tagEnd)) {
						isMultiPart = false; 
						break;
					}
					
					positionAlreadyVisited.add(tagEnd);
				}
		}
		
		if (isMultiPart) {
			int nextBoundaryEnd = emailMessage.lastIndexOf(System.getProperty("line.separator"), emailMessage.indexOf(boundaryValue, tagEnd)) + 1;
			// messagePlainTextStart = current boundaryPosition (minus some parasite lines)
			// messagePlainTextStart = get the next boundary position (last line.separator)
			//emailMessage = emailMessage.substring(nextBoundaryStart,nextBoundaryEnd);

			// TODO first lines to remove starts with 
			//Content-Type: text/plain; charset=ISO-8859-1
			//Content-Transfer-Encoding: quoted-printable
			//Content-Disposition: inline

			int newCharsetStart = charsetStart(emailMessage, 0);
			
			if (newCharsetStart !=-1) {
				int newCharsetEnd = charsetEnd(emailMessage,newCharsetStart);
				charset = getCharset(emailMessage, newCharsetStart, newCharsetEnd);
				if (!charset.toLowerCase().startsWith("iso") && !charset.toLowerCase().startsWith("utf")
						&& !charset.toLowerCase().startsWith("us-ascii")
						&& !charset.toLowerCase().startsWith("windows")) {
					Out.print("part - charset: " + charset, Out.WARN_LEVEL);
				}
			}

			int newContentTransfertEncodingStart = contentTransfertEncodingStart(emailMessage, 0);
			
			if (newContentTransfertEncodingStart != -1) {
				int newContentTransfertEncodingEnd = contentTransfertEncodingEnd(emailMessage,newContentTransfertEncodingStart);
				contentTransfertEncoding = getContentTransfertEncoding(emailMessage, newContentTransfertEncodingStart, newContentTransfertEncodingEnd);
				
				if (!contentTransfertEncoding.toLowerCase().startsWith("quoted-printable") 
						&& !contentTransfertEncoding.toLowerCase().startsWith("7bit") 
						&& !contentTransfertEncoding.toLowerCase().startsWith("base64") 
						&& !contentTransfertEncoding.toLowerCase().startsWith("8bit")) {
					Out.print("part - contentTransfertEncoding: " + contentTransfertEncoding, Out.WARN_LEVEL);
				}
			}
			
			emailMessage = emailMessage.substring(emailMessage.indexOf("\n\n",nextBoundaryStart),nextBoundaryEnd);
		} else {
			MBoxParser mboxParser = new MBoxParser();
			com.auxilii.msgparser.Message message = null;
			
			try {
				message  = mboxParser.parse(emailMessage);
				emailMessage = message.getBodyText();
			} catch (Exception e) {
				e.printStackTrace();
			}
		}

		return contentTransferDecode(emailMessage, contentTransfertEncoding, charset);
	}

	/**
	 * @param emailMessage
	 * @return
	 */
	private static String getContentTransfertEncoding(String emailMessage) {
		int contentTransfertEncodingStart = contentTransfertEncodingStart(emailMessage, 0);
		int contentTransfertEncodingEnd = contentTransfertEncodingEnd(emailMessage,contentTransfertEncodingStart);
		
		// bug Date: Mon, 15 Nov 2004 06:58:00 -0800 (PST) 	From: Regis Foinet <foinet@yahoo.fr> without messageId or contentTransferEncoding
		
		if (contentTransfertEncodingStart == -1) return "8bit";
		
		String contentTransfertEncoding = getContentTransfertEncoding(emailMessage, contentTransfertEncodingStart, contentTransfertEncodingEnd);
		
		return contentTransfertEncoding;
	}

	/**
	 * @param emailMessage
	 * @return
	 */
	private static String getCharset(String emailMessage) {
		int start = charsetStart(emailMessage, 0);
		// bug -1 due to Message-Id: <1116681891.11480.1.camel@pluton> which do not detect the end

		int end = charsetEnd(emailMessage,start-1);
		// bug Message-Id: <1112197308.10923.0.camel@localhost.localdomain> n' a pas de charset
		if (start == -1) return "UTF-8";
		String charset = getCharset(emailMessage, start, end);
		
		return charset;
	}


	/**
	 * return a name which can be used to save the current mail content 
	 */
	public static String url(Date date, String fromEmail, long lastDate) {
		//System.out.printf("%s %s %s\n",mBoxMessage.getDate().toString(), mBoxMessage.getFromName(), mBoxMessage.getSubject());
		// TODO assume that there are no consecutive emails with +1 as date difference
		String url = (date.toString().equalsIgnoreCase("")) ? new Date(lastDate+1).toString() : date.toString().replaceAll("[ ,:]", "-");

		String urlArray [] = url.split("-");
		// Wed-Sep-30-17-48-32-CEST-2009
		url = urlArray[7] + "-" + urlArray[1] + "-" + urlArray[2] + "-" + urlArray[0] + "-" + urlArray[3] + "-" + urlArray[4] + "-" + urlArray[5] + "-" + urlArray[6] + "-" + fromEmail;

		return IOUtilities.cleanFileName(url);
	}

	/**
	 * @param messageId
	 * @return
	 */
	public static  String stripMessageId (String messageId) {
		if (messageId != null ) {
			int start = messageId.indexOf("<");
			int end = messageId.indexOf(">");
			if (start == -1) start = 0; else start++;
			if (end == -1) end = messageId.length();
			
			messageId =messageId.substring(start, end);
		}
		
		return messageId; 
	}

	/* (non-Javadoc)
	 * @see java.lang.Object#toString()
	 */
	@Override
	public String toString() {
		String documentText = "";
		
		documentText += "Date: "+ getDate().toString()+ System.getProperty("line.separator");
		documentText += "Subject: "+ getSubject()+ System.getProperty("line.separator");
		documentText += "Message-Id: "+ getMessageId() + System.getProperty("line.separator");
		documentText += "From: "+ getFromName()+ "\t"+ getFromEmail()+ System.getProperty("line.separator");
		documentText += "To: "+ getToName()+ "\t"+ getToEmail()+ System.getProperty("line.separator");
		documentText += "In-Reply-To: "+ getInReplyTo() + System.getProperty("line.separator");
		documentText +=  "Text: "+ System.getProperty("line.separator")+getText();
		
		return documentText;
	}

	public static Boolean isInlineReply(String [] messageSentences) {
		// consider the presence of inline replying if there are at least two distinct reply blocks 
		String REPLY_START_PREFIX = ">";
		Boolean isReplyLine = false;
		int replyBlock = 0;
		
		for (String line : messageSentences) {
			if (line.startsWith(REPLY_START_PREFIX)) {
				if (!isReplyLine) {
					isReplyLine = true;
					replyBlock++;
				}
			} else {
				isReplyLine = false;
			}
		}
		
		if (replyBlock >= 2) return true;
		
		return false;
	}
}
