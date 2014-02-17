package email.mbox.engine;

import java.util.AbstractList;
import java.util.Vector;

import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.examples.SourceDocumentInformation;
import org.apache.uima.fit.component.JCasAnnotator_ImplBase;
import org.apache.uima.fit.descriptor.ConfigurationParameter;
import org.apache.uima.fit.descriptor.ExternalResource;
import org.apache.uima.jcas.JCas;

import com.thoughtworks.xstream.XStream;

import common.util.IO;
import common.util.Out;
import email.mbox.model.MBoxMessage;
import email.mbox.resource.MBoxResourceInterface;
import fr.univnantes.lina.javautil.IOUtilities;

/**
 * Annotator that parses the content of a JCas assuming it is an MBox message
 * Builds an internal MBox representation as a UIMA resource
 * Export each message as a digest on the file system
 * Export the resource representation which can be used for further opereration 
 */
public class MBoxResourceBuilder extends JCasAnnotator_ImplBase {
	
	public final static String RES_KEY = "aKey";
	@ExternalResource(key = RES_KEY)
	private MBoxResourceInterface mBox;

	public static final String PARAM_RESOURCE_SAVE_FILE = "resourceSaveFilename";
	@ConfigurationParameter(name = PARAM_RESOURCE_SAVE_FILE, mandatory = false, defaultValue = "/tmp/mbox.digest")
	private String resourceSaveFilename;

	public static final String PARAM_MESSAGE_SAVE_DIR = "messageSaveDir";
	@ConfigurationParameter(name = PARAM_MESSAGE_SAVE_DIR, mandatory = false, defaultValue = "")
	private String messageSaveDir;

	private static String DEFAULT_SOURCE_DOCUMENT_INFORMATION_ANNOTATION = "org.apache.uima.examples.SourceDocumentInformation";

	private int processedJCasSize = 0;
	private int processedJCasNotNullMessageIdSize = 0;

	private int inReplyToFixedBySubjectSimilarity = 0;

	private AbstractList<String> previousSubjects = new Vector<String>();
	private AbstractList<String> previousMessageIds = new Vector<String>();

	@Override
	public void initialize(org.apache.uima.UimaContext context) throws org.apache.uima.resource.ResourceInitializationException {
		Out.print("started", Out.INFO_LEVEL);
		
		super.initialize(context);

		if (messageSaveDir != null && !messageSaveDir.equalsIgnoreCase("")) {
			
			IOUtilities.deleteDirectoryContent(messageSaveDir, true);
			
			Out.print("deleted " + messageSaveDir + " folder contents", Out.INFO_LEVEL);

			//if (mappingFile != null && !mappingFile.equalsIgnoreCase("")) {
			//	deleteFile(mappingFile);
			//}
		}
	};

	@Override
	public void process(JCas aJCas) throws AnalysisEngineProcessException {
		processedJCasSize++;

		MBoxMessage mBoxMessage = new MBoxMessage(aJCas.getDocumentText());

		// process only non null cas
		// TODO decide what to do with null message ; the CR offers the possibility to process them
		if (mBoxMessage.getMessageId() != null) { 		
			processedJCasNotNullMessageIdSize++;

			/* Save the current message as a file + update a map file */ 
			if (messageSaveDir != null && !messageSaveDir.equalsIgnoreCase("")) {
				// Get the uri of the current jcas
				SourceDocumentInformation sourceDocumentInformation = (SourceDocumentInformation) aJCas.getAnnotationIndex(aJCas.getTypeSystem().getType(DEFAULT_SOURCE_DOCUMENT_INFORMATION_ANNOTATION)).iterator().get();
				String uri = sourceDocumentInformation.getUri();
				//MiscUtil.writeToFS(mBoxMessage.toString(), messageSaveDir+"/"+uri, false);
				XStream xstream = new XStream(); 
				String xmlHeader = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+"\n";
				String snippet = xstream.toXML(mBoxMessage);

				// the following do not escape the whitespace char
				//System.out.println("Debug: escapeXml "+ StringEscapeUtils.escapeXml(snippet));
				
				// CR/LF/tab http://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references
				//snippet = snippet.replaceAll("\\n", "&#10;").replaceAll("\\r", "&#13;").replaceAll("\\t", "&#9;");

				String xml = xmlHeader+snippet;
				IO.write(xml, messageSaveDir+"/"+uri, false);
				
				mBox.addMessageFilenameMapping(mBoxMessage.getMessageId(), uri);
			} else {
				Out.print("this messageId has not been saved on the file system " + mBoxMessage.getMessageId(), Out.WARN_LEVEL);
			}

			/* Populate the resource */
			mBox.setMessage(mBoxMessage.getMessageId());

			/** Set is posting style inline replying */
			// consider the presence of inline replying if there are at least two distinct reply blocks 
			if (MBoxMessage.isInlineReply( mBoxMessage.getText().split("\n"))) {
				mBox.setInlineReplying(mBoxMessage.getMessageId());
			}
			
			/** Set the structure based on in reply to and subject similarity */
			String inReplyTo = mBoxMessage.getInReplyTo();
			
			if (inReplyTo.contains(" ")) {
				Out.print("this inReplyTo id contains whitespace character, probably '+' chars removed, about to be fixed:" + inReplyTo, Out.WARN_LEVEL);

				// BUG 
				// first message:
				// Message-ID: <AANLkTin=6Qumu4oqCvotxUDU-dHfq+OWE6=UKqG2r9WG@mail.gmail.com>
				// reply message:
				// In-Reply-To: <AANLkTin=6Qumu4oqCvotxUDU-dHfq OWE6=UKqG2r9WG@mail.gmail.com>
				// Message-ID: <0016368337a01141960492868622@google.com>
				// the '+' char has been removed... why ?
				// Warning: this inReplyTo id >AANLkTin=6Qumu4oqCvotxUDU-dHfq OWE6=UKqG2r9WG@mail.gmail.com< contains whitespace character
				// Warning: this inReplyTo id >AANLkTinbADO-0kpoviG==tV8a vQ6X2MMShZd=6ujeuK@mail.gmail.com< contains whitespace character
				// Warning: this inReplyTo id >AANLkTik9h-thKOQPBiB8sxsNx dY iFiHNgGPZ6hn1CS@mail.gmail.com< contains whitespace character
				// it concerns three messages, we decide to fix them
				inReplyTo = inReplyTo.replaceAll(" ", "+");
			}

			// list LIFO of subjects
			// at most n subjects
			int subjectBufferSize = 10;
			String subjectDigest = mBoxMessage.getSubject();

			//  subjectDigest is used to link mails when no inReplyTo information is found but when Re: is found in the subject
			if (subjectDigest != null) subjectDigest = subjectDigest.replaceAll("\\P{L}", "").replaceAll("^(Re)+", "").toLowerCase();

			if (inReplyTo.equalsIgnoreCase("")) {
				// no in-reply-to but presence of Re: in the subject... 
				// we look for the first similar subject in the list and if this is the case we associate it 
				if (mBoxMessage.getSubject() != null && mBoxMessage.getSubject().startsWith("Re:")) {
					inReplyToFixedBySubjectSimilarity++;

					for (int i = previousSubjects.size()-1 ; i >=0 ; i--) {
						if (previousSubjects.get(i).equalsIgnoreCase(subjectDigest)) {
							inReplyTo = previousMessageIds.get(i);
							mBox.setRepliedBy (inReplyTo, mBoxMessage.getMessageId());
							mBox.setRepliesTo(mBoxMessage.getMessageId(), inReplyTo);
							break;
						}
					}
				} else {
					// initiate a thread
					mBox.setInitialThreadMessage(mBoxMessage.getMessageId());
				}
			} else { 
				mBox.setRepliedBy (inReplyTo, mBoxMessage.getMessageId());
				mBox.setRepliesTo(mBoxMessage.getMessageId(), inReplyTo);
			}

			// maintain a ordered buffer of previous subjects (digests) 
			if (subjectDigest != null) {
				if (previousSubjects.size() == subjectBufferSize) previousSubjects.remove(0); // remove the element at the specified position and the shift to the left
				previousSubjects.add(subjectDigest); // append to the end of the list 
				if (previousMessageIds.size() == subjectBufferSize) previousMessageIds.remove(0); // remove the element at the specified position and the shift to the left
				previousMessageIds.add(mBoxMessage.getMessageId()); // append to the end of the list 
			}
		}
	}

	@Override
	public void collectionProcessComplete()  throws AnalysisEngineProcessException {
		// Prints the instance ID to the console - this proves the same instance
		// of the SharedModel is used in both Annotator instances.
		Out.print("# of processed JCas: " + processedJCasSize );
		Out.print("# of processed JCas without a null messageId: " + processedJCasNotNullMessageIdSize, Out.INFO_LEVEL);
		Out.print("# of messages without inReplyTo but fixed by subject similarity: " + inReplyToFixedBySubjectSimilarity, Out.INFO_LEVEL);
		Out.print("# of threads: " + mBox.getInitialThreadMessages().size(), Out.INFO_LEVEL);

		/* Save the mbox representation */
		mBox.save(resourceSaveFilename);
		
		Out.print("done", Out.INFO_LEVEL);
	}
}
