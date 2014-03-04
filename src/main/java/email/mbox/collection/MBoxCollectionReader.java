package email.mbox.collection;

import java.io.File;
import java.io.IOException;
import java.io.StringWriter;
import java.nio.charset.Charset;
import java.nio.charset.CharsetEncoder;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;

import org.apache.commons.io.IOUtils;
import org.apache.james.mime4j.mboxiterator.CharBufferWrapper;
import org.apache.james.mime4j.mboxiterator.MboxIterator;
import org.apache.uima.UimaContext;
import org.apache.uima.collection.CollectionException;
import org.apache.uima.examples.SourceDocumentInformation;
import org.apache.uima.fit.component.JCasCollectionReader_ImplBase;
import org.apache.uima.fit.descriptor.ConfigurationParameter;
import org.apache.uima.jcas.JCas;
import org.apache.uima.resource.ResourceInitializationException;
import org.apache.uima.util.Progress;

import com.auxilii.msgparser.Message;

import common.util.Out;
import email.mbox.model.MBoxMessage;
import factory.parser.MBoxParser;

/**
 * This reader reads messages from a mbox file
 */
public class MBoxCollectionReader extends JCasCollectionReader_ImplBase {
	
	/** Path of the mbox file whose messages should be turned into JCas*/
	public static final String PARAM_MBOX_SRCPATH = "mboxSrcPath";
	@ConfigurationParameter(name = PARAM_MBOX_SRCPATH, mandatory = true)
	private String mboxSrcPath;

	/** Main language of the messages contained in the mbox file*/
	public static final String PARAM_LANGUAGE = "language";
	@ConfigurationParameter(name = PARAM_LANGUAGE, mandatory = false, defaultValue = "fr")
	private String language;

	/** Main encoding of the messages contained in the mbox file*/
	public static final String PARAM_ENCODING = "encoding";
	@ConfigurationParameter(name = PARAM_ENCODING, mandatory = false, defaultValue = "utf-8")
	private String encoding;

	/** Create a JCas for null message Id in the mbox file*/
	public static final String PARAM_AS_JCAS_NULL_MSG_ID = "nullMsgIdAsJCas";
	@ConfigurationParameter(name = PARAM_AS_JCAS_NULL_MSG_ID, mandatory = false, defaultValue = "false")
	private Boolean nullMsgIdAsJCas;

	private static CharsetEncoder CHARSET_ENCODER; 

	private Iterator<CharBufferWrapper> mboxIterator;

	private int messageIndex = 0;

	private int msgWiNullId = 0;

	private long lastDate = -1;

	private Set<String> messageIdUrlAlreadyCreated = new HashSet<String>();
	
	public static boolean close_prints = false;
	
	/**
	 * Get a list of the urls contained in the zim file
	 */
	@Override
	public void initialize(final UimaContext context) throws ResourceInitializationException {
		Out.print("started", Out.INFO_LEVEL);
		
		CHARSET_ENCODER = Charset.forName(encoding).newEncoder();

		// Get the mbox file from the path
		final File mbox = new File(mboxSrcPath);
		
		try {
			mboxIterator = MboxIterator.fromFile(mbox).charset(CHARSET_ENCODER.charset()).build().iterator();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	/**
	 * @see org.apache.uima.collection.CollectionReader#hasNext()
	 */
	public boolean hasNext() {
		return mboxIterator.hasNext();
	}

	/**
	 * For each url of the zim file
	 */
	@Override
	public  void getNext(JCas jCas) throws IOException, CollectionException {
		String documentText = "";
		String messageId = null;
		String fakeMessageId = "";

		Boolean firstTime = true;

		// by AE parameter we decide if we create a cas for null message id message
		// by default 
		// seems not to work since we force the creation of an id 
		// TODO to remove : always create or to fix 
		while ((!nullMsgIdAsJCas && messageId == null) || firstTime) {
			documentText = "";

			if (!firstTime) Out.print("as required by parameter no CAS created for (probably a null value) " + fakeMessageId,  Out.INFO_LEVEL);
			
			firstTime = false;

			CharBufferWrapper message = mboxIterator.next();

			StringWriter writer = new StringWriter();
			IOUtils.copy(message.asInputStream(CHARSET_ENCODER.charset()), writer);
			String messageContent = writer.toString();

			// the end of the string has some \0 added probably due to CharBufferWrapperso we remove it
			int slashZeroStart = messageContent.indexOf("\0");
			if (slashZeroStart != -1) {
				messageContent = messageContent.substring(0, slashZeroStart);
			}

			// the mbox file is segmented in messages 
			// for further processing as a small mbox we had to add the mbox envelope arround each message
			// e.g. "From bruno.sapene@free.fr Mon Sep 27 03:30:44 2004";
			// finally we will not process as a mbox
			// http://www.qmail.org/man/man5/mbox.html

		
			documentText += new String(messageContent.getBytes("UTF-8"));


			//Message-Id: ou Message-ID ou Message-id:
			MBoxParser mboxParser = new MBoxParser();
			Message messageSource = null;
			
			try {
				messageSource  = mboxParser.parse(documentText);
			} catch (Exception e) {
				e.printStackTrace();
			}
			
			messageId = MBoxMessage.stripMessageId(messageSource.getMessageId());
			
			// bug From mohamed.mahmoudi@nordnet.fr Sat Aug 14 11:36:50 2010 do not have a message-id
			if (messageId == null) {
				msgWiNullId++;
				
				Out.print("messageId is null in the current message", Out.WARN_LEVEL);
			}
			
			messageId = MBoxMessage.url(messageSource.getDate(), messageSource.getFromEmail(), lastDate);

			if (messageIdUrlAlreadyCreated.contains(messageId)) {
				Out.print("the messageId " + messageId + " has already been generated", Out.WARN_LEVEL);
			} else {
				messageIdUrlAlreadyCreated.add(messageId);
			}

			lastDate = messageSource.getDate().getTime();
		}

		jCas.setDocumentText(documentText);

		// set language if it was explicitly specified as a configuration parameter
		if (language != null) jCas.setDocumentLanguage(language);
		
		// Also store location of source document in CAS. This information is critical
		// if CAS Consumers will need to know where the original document contents are located.
		// For example, the Semantic Search CAS Indexer writes this information into the
		// search index that it creates, which allows applications that use the search index to
		// locate the documents that satisfy their semantic queries.
		
		SourceDocumentInformation srcDocInfo = new SourceDocumentInformation(jCas);
		
		srcDocInfo.setUri(messageId);
		srcDocInfo.setOffsetInSource(0);
		srcDocInfo.setDocumentSize(documentText.length());
		srcDocInfo.setLastSegment(false); // TODO cannot know when the last segment is encountered with an iterator
		srcDocInfo.addToIndexes();
		
		messageIndex++;
	}

	/**
	 * @see org.apache.uima.collection.base_cpm.BaseCollectionReader#close()
	 */
	public void close() throws IOException {
		// Hack to prevent multiple prints
		if (!close_prints) {
			Out.print("# of created JCas: " + messageIndex, Out.INFO_LEVEL);
			Out.print("# of message with a null id: " + msgWiNullId, Out.INFO_LEVEL);
			Out.print("done", Out.INFO_LEVEL);
			
			close_prints = true;
		}
	}

	/**
	 * @see org.apache.uima.collection.base_cpm.BaseCollectionReader#getProgress()
	 */
	public Progress[] getProgress() {
		return new Progress[messageIndex] ;
	}

	/**
	 * Gets the total number of documents that will be returned by this collection reader. This is not
	 * part of the general collection reader interface.
	 * 
	 * @return the number of documents in the collection
	 */
	public int getNumberOfDocuments() {
		return messageIndex;
	}
}