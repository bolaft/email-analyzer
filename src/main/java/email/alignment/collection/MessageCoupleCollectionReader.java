package email.alignment.collection;

import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import org.apache.uima.UimaContext;
import org.apache.uima.collection.CollectionException;
import org.apache.uima.examples.SourceDocumentInformation;
import org.apache.uima.fit.component.JCasCollectionReader_ImplBase;
import org.apache.uima.fit.descriptor.ConfigurationParameter;
import org.apache.uima.fit.descriptor.ExternalResource;
import org.apache.uima.jcas.JCas;
import org.apache.uima.util.Progress;

import com.thoughtworks.xstream.XStream;

import common.util.IO;
import common.util.Out;
import email.mbox.model.MBoxMessage;
import email.mbox.resource.MBoxResourceInterface;
import email.types.Message;

/**
 * This reader reads messages from a mbox file
 */
public class MessageCoupleCollectionReader extends JCasCollectionReader_ImplBase
{
	public final static String RES_KEY = "mBoxResource";
	@ExternalResource(key = RES_KEY)
	private MBoxResourceInterface mBox;

	/** Path dir where the message files are*/
	public static final String PARAM_MSG_DIR_PATH = "messageDirPath";
	@ConfigurationParameter(name = PARAM_MSG_DIR_PATH, mandatory = true)
	private String messageDirPath;

	/** Path dir where the couple of messages can be exported */
	public static final String PARAM_MSG_CPL_DIR_PATH = "messageCplDirPath";
	@ConfigurationParameter(name = PARAM_MSG_CPL_DIR_PATH, mandatory = false)
	private String messageCplDirPath;

	/** Main language of the messages contained in the mbox file*/
	public static final String PARAM_LANGUAGE = "language";
	@ConfigurationParameter(name = PARAM_LANGUAGE, mandatory = false, defaultValue = "fr")
	private String language;

	private int messageIndex = 0;

	private Map<String,String> messageIdCoupleMap;

	private Iterator<String> filenameMessageCoupleKeySetIterator;

	private Set<String> messageWithoutFilename;

	/**
	 * Get a list of the urls contained in the zim file
	 */
	@Override
	public void initialize(final UimaContext context) {
		// create couples made of message with inline reply and its source filename
		// the key is the source message id and the value is the reply message id
		messageWithoutFilename  = new HashSet<String>();
		messageIdCoupleMap = new HashMap<String,String>();
		
		Out.print("started", Out.INFO_LEVEL);
		
		Out.print("inlineReplyingSize: " + mBox.getInlineReplying().size());

		for (String inlineReplyingMessageId : mBox.getInlineReplying()) {

			if (mBox.getMessageIdToFilenameMapping().containsKey(inlineReplyingMessageId)) {
				
				String messageIdRepliedBy = mBox.getMessageIdRepliedBy(inlineReplyingMessageId);

				if (messageIdRepliedBy != null) {
						if (mBox.getMessageIdToFilenameMapping().containsKey(messageIdRepliedBy) ) {
							messageIdCoupleMap.put(messageIdRepliedBy, inlineReplyingMessageId);
						} else {
							Out.print("replyId " + inlineReplyingMessageId + " (of the sourceId " + messageIdRepliedBy + ") does not have a filename correspondance", Out.WARN_LEVEL);
							messageWithoutFilename.add(messageIdRepliedBy);
						}
				} else {
					Out.print("replyId " + inlineReplyingMessageId + " (of the sourceId " + messageIdRepliedBy + ") has a null value", Out.WARN_LEVEL);
					messageWithoutFilename.add(messageIdRepliedBy);
				}
			} else {
				Out.print("sourceId (repliedByMessages.key) " + inlineReplyingMessageId + " does not have a filename correspondance", Out.WARN_LEVEL);
				messageWithoutFilename.add(inlineReplyingMessageId);
			}
		}

		filenameMessageCoupleKeySetIterator = messageIdCoupleMap.keySet().iterator();
		
		/*
		CHARSET_ENCODER = Charset.forName(encoding).newEncoder();

		// Get the mbox file from the path
		final File coupleOfMBoxMessageDirFile = new File(coupleOfMBoxMessageDirPath);

		if (coupleOfMBoxMessageDirFile.exists() && coupleOfMBoxMessageDirFile.isDirectory()) {
			coupleOfMboxMessageFileList = coupleOfMBoxMessageDirFile.listFiles();

		}
		 */
	}

	/**
	 * @see org.apache.uima.collection.CollectionReader#hasNext()
	 */
	public boolean hasNext() {
		return filenameMessageCoupleKeySetIterator.hasNext();
	}

	/**
	 * For each url of the zim file
	 */
	@Override
	public  void getNext(JCas jCas) throws IOException, CollectionException {
		String sourceId = filenameMessageCoupleKeySetIterator.next();
		String replyId = messageIdCoupleMap.get(sourceId);
		String url = mBox.getFilename(sourceId)+"_"+mBox.getFilename(replyId);
		
		Out.print("URL: " + url);

		// first part 
		String firstPartUrl = messageDirPath + "/" + mBox.getFilename(sourceId);
		// http://xstream.codehaus.org/faq.html#XML_attribute_normalization
		// I find out that carriage return and line feed characters are replaced with normal spaces.
		// If you want to keep these characters you will have to encode them with entities.
		String firstPart = IO.read(firstPartUrl);
		XStream xstream = new XStream();
		MBoxMessage firstPartMBoxMessage = (MBoxMessage) xstream.fromXML(firstPart);
		firstPart = firstPartMBoxMessage.getText();

		// second part 
		String secondPartUrl =  messageDirPath + "/" + mBox.getFilename(replyId);
		String secondPart = IO.read(secondPartUrl);
		MBoxMessage secondPartMBoxMessage = (MBoxMessage) xstream.fromXML(secondPart);
		secondPart = secondPartMBoxMessage.getText();


		String documentText = firstPart+"\n"+secondPart;

		jCas.setDocumentText(documentText);

		// set language if it was explicitly specified as a configuration parameter
		if (language != null) jCas.setDocumentLanguage(language);

		// Also store location of source document in CAS. This information is critical
		// if CAS Consumers will need to know where the original document contents are located.
		// For example, the Semantic Search CAS Indexer writes this information into the
		// search index that it creates, which allows applications that use the search index to
		// locate the documents that satisfy their semantic queries.
		SourceDocumentInformation srcDocInfo = new SourceDocumentInformation(jCas);
		srcDocInfo.setUri(url);
		srcDocInfo.setOffsetInSource(0);
		srcDocInfo.setDocumentSize(documentText.length());
		srcDocInfo.setLastSegment(false); // TODO cannot know when the last segment is encountered with an iterator
		srcDocInfo.addToIndexes();

		Message msg1 = new Message(jCas);
		msg1.setBegin(0);
		msg1.setEnd(firstPart.length());
		msg1.addToIndexes();

		Message msg2 = new Message(jCas);
		msg2.setBegin(firstPart.length());
		msg2.setEnd(documentText.length());
		msg2.addToIndexes();

		messageIndex++;

		// TODO to debug in order to process only one couple
		//while (filenameMessageCoupleKeySetIterator.hasNext()) {
		//	filenameMessageCoupleKeySetIterator.next();
		//}
	}

	/**
	 * @see org.apache.uima.collection.base_cpm.BaseCollectionReader#close()
	 */
	public void close() throws IOException {
		Out.print("# of message with a corresponding file: " + mBox.getMessageIdToFilenameMapping().size(), Out.INFO_LEVEL);
		Out.print("# of messageId without a filename correspondance: " + messageWithoutFilename.size(), Out.INFO_LEVEL);
		Out.print("# of couple of messageId effectively created (both with a filename correspondance): " + messageIdCoupleMap.size(), Out.INFO_LEVEL);
		
		Out.print("done", Out.INFO_LEVEL);
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