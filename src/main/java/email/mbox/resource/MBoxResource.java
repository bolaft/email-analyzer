package email.mbox.resource;

import java.io.File;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

import org.apache.uima.resource.DataResource;
import org.apache.uima.resource.ResourceInitializationException;
import org.apache.uima.resource.SharedResourceObject;

import com.thoughtworks.xstream.XStream;
import com.thoughtworks.xstream.io.xml.StaxDriver;

import common.util.IO;
import common.util.Out;
import fr.univnantes.lina.javautil.IOUtilities;

/**
 * Implementation of the resource model for Email Message Box
 */
public final class MBoxResource implements MBoxResourceInterface, SharedResourceObject {

	/** set of all the message-id */
	Set<String> messagesSet;

	/** set of message-id starting a thread (with no in-reply-to line in the header) */
	Set<String> initialThreadMessage;

	/** set of message-id replies of a given message-id (map from message-id to a set of message-id replies */
	Map<String, Set<String>> repliedBy;

	/** message-id of a given in-reply-to message-id (map) */
	Map<String, String> repliesTo;

	/** number if messageId with unexpected null value (due to wrong message format)*/
	int numberOfNullMessageId = 0;

	/** message depth in a thread (can be computed a posteriori with recursive repliesTo) */
	// TODO
	
	/** mapping from messageId to filename */
	Map<String, String> messageIdToFilenameMapping;

	/** set of message-id which may be are inline replying based on an heuristic (at least two distinct block of reply lines) */
	Set<String> inlineReplyingSet;
	
	private Boolean isLoaded = false;
	private Boolean isSaved = false;

	private String VISUAL_DEPTH_SEPARATOR = "  ";
	private String ID_MESSAGE_SEPARATOR = "\t";

	private final String InitialThreadMessageIdTag = "# <InitialThreadMessageId/>";
	private final String RepliedBySetOfReplyToTag = "# <RepliedBySetOfReplyTo/>";
	private final String RepliedToTag = "# <RepliedTo/>";
	private final String RepliedByNotFirstReplyToCoupleTag = "# <RepliedByNotFirstReplyToCouple/>";
	private final String ThreadTreeStructureTag = "# <ThreadTreeStructure/>";
	private final String GlobalStatisticsTag = "# <GlobalStatistics/>";
	private final String NumberOfNullMessageIdTag = "# <NumberOfNullMessageIdTag/>";
	private final String messageIdToFilenameMappingSectionTag = "# <MappingMessageIdToFilename/>";
	
	/**
	 * @return the messageIdToFilenameMapping
	 */
	@Override
	public synchronized Map<String, String> getMessageIdToFilenameMapping() {
		return messageIdToFilenameMapping;
	}

	@Override
	public synchronized Set<String> getMessages() {
		return messagesSet;
	}

	@Override
	public synchronized Set<String> getInitialThreadMessages() {
		return initialThreadMessage;
	}

	@Override
	public synchronized Map<String, Set<String>> getRepliedBy () {
		return repliedBy;
	}

	@Override
	public synchronized Set<String> getMessagesIdWhichRepliesTo(String messageIdRepliedBy) {
		/** not all the messageIdRepliedBy has been replied so if their repliesTo are asked, we should return new HashSet/LinkedHashSet  */
		return getRepliedBy().containsKey(messageIdRepliedBy) ? getRepliedBy().get(messageIdRepliedBy) : new LinkedHashSet<String>();
	}

	@Override
	public synchronized Map<String, String> getRepliesTo () {
		return repliesTo;
	}

	@Override
	public synchronized String getMessageIdRepliedBy(String messageIdReplyTo) {
		return getRepliesTo().get(messageIdReplyTo);
	}

	@Override
	public synchronized void setMessage(String messageId) {
		// add it even if exists (avoid to test its presence)
		if (messageId != null) {
			String strippedMessageId = strip(messageId);

			getMessages().add(strippedMessageId);
		} else {
			Out.print("setMessage " + messageId + " - attempt to set a null value", Out.WARN_LEVEL);
			incNumberOfNullMessageId();
		}
	}

	@Override
	public synchronized void setInitialThreadMessage(String messageId) {
		if (messageId != null) {
			String strippedMessageId = strip(messageId);
			getInitialThreadMessages().add(strippedMessageId);
		} else {
			Out.print("setInitialThreadMessage " + messageId + " - attempt to set a null value", Out.WARN_LEVEL);
		}
	}

	@Override
	public synchronized void setRepliedBy(String messageIdRepliedBy, String messageIdReplyTo) {
		// TODO should also test if messageIdReplyTo is present as message 		
		if (messageIdRepliedBy != null && messageIdReplyTo != null) {
			String strippedMessageIdReplyTo = strip(messageIdReplyTo);
			String strippedMessageIdRepliedBy = strip(messageIdRepliedBy);

			Set<String> repliedBySet = getRepliedBy().get(strippedMessageIdRepliedBy);
			
			if (repliedBySet == null) repliedBySet = new LinkedHashSet<String>();
			
			repliedBySet.add(strippedMessageIdReplyTo);
			getRepliedBy().put(strippedMessageIdRepliedBy, repliedBySet);
		} else {
			Out.print("set " + messageIdRepliedBy + " is replied to " + messageIdReplyTo + " - attempt to set a null value", Out.WARN_LEVEL);
		}
	}

	@Override
	public synchronized void setRepliesTo(String messageIdReplyTo, String messageIdRepliedBy) {
		// TODO should also test if messageIdReplyTo is present as message 		
		if (messageIdRepliedBy != null && messageIdReplyTo != null) {
			String strippedMessageIdReplyTo = strip(messageIdReplyTo);
			String strippedMessageIdRepliedBy = strip(messageIdRepliedBy);
			getRepliesTo().put(strippedMessageIdReplyTo, strippedMessageIdRepliedBy);
		} else {
			Out.print("set " + messageIdReplyTo + " replies to " + messageIdRepliedBy + " - attempt to set a null value", Out.WARN_LEVEL);
		}
	}


	/** InitialThreadMessageId to string */ 
	public synchronized String initialThreadMessageIdToString() {
		String output = "";
		output += InitialThreadMessageIdTag + "\n";
		
		for (String initialThreadMessage : getInitialThreadMessages()) {
			output += initialThreadMessage + "\n";
		}
		
		return output;
	}

	/**  RepliedBy Set Of ReplyTo to string */ 
	public synchronized String repliedBySetOfReplyToToString() {
		String output = "";
		output += RepliedBySetOfReplyToTag+"\n";
		output += "# format\n" + "# repliedById[ replyToId]*\n";
		
		for (String repliedById : getRepliedBy().keySet()) {
			Set<String> repliesToIdSet = getMessagesIdWhichRepliesTo(repliedById);
			output += repliedById;
			
			for (String replyToId : repliesToIdSet) output += ID_MESSAGE_SEPARATOR+replyToId;
			
			output += "\n";
		}
		
		return output;
	}

	/** RepliedTo to string */ 
	public synchronized String repliedToToString() {
		String output = "";

		/* RepliedTo */ 
		output += RepliedToTag+"\n";
		output += "# format\n" + "# replyToId repliedById\n";
		for (String replyToId : getRepliesTo().keySet()) {
			output += replyToId+ID_MESSAGE_SEPARATOR+getMessagesIdWhichRepliesTo(replyToId) + "\n";
		}
		
		return output;
	}

	/** numberOfNullMessageId to string */ 
	public synchronized String numberOfNullMessageIdToString() {
		String output = "";

		output += NumberOfNullMessageIdTag + "\n";
		output += String.valueOf(getNumberOfNullMessageId()) + "\n";

		return output ;
	}

	/** RepliedByNotFirstReplyToCouple to string */ 
	public synchronized String repliedByNotFirstReplyToCoupleToString() {
		String output = "";

		/* List of message Id couples (a message and one of its replies) 
		 * except the first one of a thread */
		// to make a list of a couple per line and message-id separated by a specific character. 
		// The first message-id stands for the request message and the second for its reply. 
		// message-id-replied-by	message-id-in-reply-to
		// does not contain the first reply to the initial message  
		output += RepliedByNotFirstReplyToCoupleTag + "\n";
		
		for (String messageId : getMessages()) {
			String repliedBy =  getMessageIdRepliedBy(messageId);
			if (repliedBy != null) {
				// if the repliedBy is the first message of a thread
				if (getInitialThreadMessages().contains(repliedBy)) {
					Iterator<String> repliesToIterator = getMessagesIdWhichRepliesTo(repliedBy).iterator();
					// since repliedBy != null, we do not need to test the following
					// if (repliesToIterator.hasNext()) 
					// if the current message is not the first reply
					if (! repliesToIterator.next().equalsIgnoreCase(messageId))	output += repliedBy+ID_MESSAGE_SEPARATOR+messageId + "\n";
				} else {
					output += repliedBy+ID_MESSAGE_SEPARATOR+messageId + "\n";
				}
			}
		}
		
		return output;
	}

	/**
	 * return the max depth of the descendant given a message ID
	 * Used to compute the depth of a thread with initial thread message id 
	 * @param depth
	 * @param messageId
	 * @return
	 */
	public int descendantDepth (Integer depth, String messageId) {
		int maxDepth = depth; 
		
		for (String repliedBy : getMessagesIdWhichRepliesTo(messageId)) {
			int currentDepth = descendantDepth (depth, repliedBy);
			if (currentDepth > maxDepth) maxDepth = currentDepth;
		}
		
		return maxDepth+1;
	}

	/**
	 * return a visual tree presentation of the thread structure
	 * @param depth
	 * @param messageId
	 * @return
	 */
	public String threadTreeStructureEcho (Integer depth, String messageId) {
		String output = "";
		
		// TODO ne lève pas d'exception quand il y a le if 
		// mais des messageId ne sont pas présents
		// pourquoi sont ils en null ? 
		//if (getRepliesTo(messageId) != null ) {
		//System.out.printf("Debug depth %d messageId %s %s %s\n", depth, messageId,	
		//		getRepliedBy().containsKey(messageId) ? "containsKey" : "notContainsKey",
		//		getRepliedBy().get(messageId) == null ? "repliedByNull" : "repliedByNotNull");
		
		for (int i = 0 ; i < depth ; i++) {
			output += VISUAL_DEPTH_SEPARATOR;
		}
		
		output += messageId+"\n";
		
		depth++;
		
		for (String repliedBy : getMessagesIdWhichRepliesTo(messageId)) {
			output += threadTreeStructureEcho (depth, repliedBy);
		}
		
		return output;
	}

	/**
	 * echo a human readable report of the mbox resource 
	 * + a visual tree structure for each threads
	 * + some statistics
	 */
	public synchronized String threadTreeStructurePlusGlobalStatisticsToString() {
		String output = "";

		/* tree structure of each thread */
		/* sum max depth */
		output += ThreadTreeStructureTag+"\n";
		
		for (String initialThreadMessage : getInitialThreadMessages()) {
			String currentOutput = threadTreeStructureEcho (0, initialThreadMessage);
			
			int threadMessageCounter = (currentOutput.split("\n")).length;
			
			output += currentOutput;
			output += "# messages "+ threadMessageCounter+"\n";
		}

		/* sum of node degree i.e. number of repliesTo 
		 * to compute latter the average */
		float repliesToSum = 0;
		
		for (String messageIdRepliedBy : getRepliedBy().keySet()) {
			Set<String> repliesTo = getMessagesIdWhichRepliesTo(messageIdRepliedBy);
			repliesToSum += repliesTo.size();
		}
		
		float nodeDegree = (repliesToSum / getRepliedBy().keySet().size());

		/* average node degree when there are replies to*/
		float	averageNodeDegreeWhenRepliesToExist = 0;
		int numberOfNodeWithReplyTo = 0;
		
		for (String messageIdRepliedBy : getRepliedBy().keySet()) {
			Set<String> repliesTo = getMessagesIdWhichRepliesTo(messageIdRepliedBy);
			if (!repliesTo.isEmpty()) {
				averageNodeDegreeWhenRepliesToExist += repliesTo.size();
				numberOfNodeWithReplyTo++;
			}
		}
		
		averageNodeDegreeWhenRepliesToExist /= numberOfNodeWithReplyTo;

		float averageDepthWiSingleMessageThread = 0;
		
		for (String initialThreadMessage : getInitialThreadMessages()) {
			averageDepthWiSingleMessageThread += descendantDepth(0, initialThreadMessage);
		}
		
		averageDepthWiSingleMessageThread /= getInitialThreadMessages().size();

		/* average depth without single message thread */
		float averageDepthWoSingleMessageThread= 0;
		int initialThreadMessagesWoSingleMessageThreadCounter = 0;
		
		for (String initialThreadMessage : getInitialThreadMessages()) {
			if (!getMessagesIdWhichRepliesTo(initialThreadMessage).isEmpty()) {
				averageDepthWoSingleMessageThread += descendantDepth(0, initialThreadMessage);
				initialThreadMessagesWoSingleMessageThreadCounter++;
			}
		}
		
		averageDepthWoSingleMessageThread /= initialThreadMessagesWoSingleMessageThreadCounter;

		/*Average # of messages per thread*/
		float averageNumberOfMessagesPerThread = ((float) ((float) getRepliesTo().keySet().size() + (float) getInitialThreadMessages().size())/(float) getInitialThreadMessages().size()) ;
		
		/* final outputs */
		output += GlobalStatisticsTag + "\n";
		output += "Total # threads " + getInitialThreadMessages().size() + "\n";
		output += "Total # messages " + (getRepliesTo().keySet().size() + getInitialThreadMessages().size()) + "\n";
		output += "Average # of messages per thread " + averageNumberOfMessagesPerThread + "\n";
		output += "Total # reply messages " + getRepliesTo().keySet().size() + "\n";
		output += "Average # of reply messages per replied message (node degree) " + nodeDegree + "\n";
		output += "Average # of reply messages per replied message (with reply) " + averageNodeDegreeWhenRepliesToExist + "\n";
		output += "Average depth of a thread with single message thread " + averageDepthWiSingleMessageThread + "\n";
		output += "Average depth of a thread without single message thread " + averageDepthWoSingleMessageThread + "\n";
		output += "Total # of NullMessageId " + getNumberOfNullMessageId() + "\n";

		return output;
	}

	/* RepliedByNotFirstReplyToCouple to string */ 
	public synchronized String messageIdFilenameMappingToString() {
		String output = "";

		/* List of message Id couples (a message and one of its replies) 
		 * except the first one of a thread */
		// to make a list of a couple per line and message-id separated by a specific character. 
		// The first message-id stands for the request message and the second for its reply. 
		// message-id-replied-by	message-id-in-reply-to
		// does not contain the first reply to the initial message  
		output += messageIdToFilenameMappingSectionTag + "\n";
		
		for (String messageId : getMessageIdToFilenameMapping().keySet()) {
			String filename =  getMessageIdToFilenameMapping().get(messageId);
			output += messageId+ID_MESSAGE_SEPARATOR+filename + "\n";
		}
		
		return output;
	}

	/**
	 * Echo all the necessary pieces of information 
	 * that are required to re build the resource
	 * and more
	 */
	public synchronized String toString() {
		String output = "";

		output += initialThreadMessageIdToString();
		output += repliedBySetOfReplyToToString();
		output += repliedToToString();
		output += numberOfNullMessageIdToString();
		output += repliedByNotFirstReplyToCoupleToString();
		output += threadTreeStructurePlusGlobalStatisticsToString();
		output += messageIdFilenameMappingToString();

		return output;
	}


	/**
	 * @return the isSaved
	 */
	public synchronized Boolean isSaved() {
		return isSaved;
	}

	/**
	 * @param isSaved the isSaved to set
	 */
	public synchronized void setIsSaved(Boolean isSaved) {
		this.isSaved = isSaved;
	}

	/**
	 * @return the alreadyLoaded
	 */
	public synchronized Boolean isLoaded() {
		return this.isLoaded;
	}

	/**
	 * @param alreadyLoaded the alreadyLoaded to set
	 */
	public synchronized void setLoaded(Boolean isLoaded) {
		this.isLoaded = isLoaded;
	}

	/**
	 * Save the content of the resource as a CSV file
	 * a line per word, word and counter as columns with tab character as separator
	 * use the MiscUtil.writeToFS(textString,filenameString) 
	 */
	public synchronized void save(String filename){
		if (!isSaved()) {
			XStream xstream = new XStream(); 
			String xml = xstream.toXML(this);
			IO.write(xml,filename, false);

			setIsSaved(true);
		}
	}

	public synchronized void load(DataResource aData) throws ResourceInitializationException {
		if (!isLoaded()) {
			messagesSet = new LinkedHashSet<String>();
			initialThreadMessage = new LinkedHashSet<String>();
			repliedBy = new HashMap<String,Set<String>>();
			repliesTo = new HashMap<String,String>();
			inlineReplyingSet = new LinkedHashSet<String>();
			messageIdToFilenameMapping  = new HashMap<String,String>();
			
			File f = new File (aData.getUri().toString());
			
			if (f.exists()) {
				// TODO to test Deserializing an object back from XML
				String xml = IOUtilities.readTextFileAsString(aData.getUri().toString());
				XStream xstream = new XStream(new StaxDriver()); 
				MBoxResourceInterface deserializedResource = (MBoxResourceInterface) xstream.fromXML(xml);
				
				messagesSet = deserializedResource.getMessages();
				initialThreadMessage = deserializedResource.getInitialThreadMessages();
				repliedBy = deserializedResource.getRepliedBy();
				repliesTo = deserializedResource.getRepliesTo();
				messageIdToFilenameMapping = deserializedResource.getMessageIdToFilenameMapping();
				inlineReplyingSet = deserializedResource.getInlineReplying();
			}
			
			setLoaded(true);
		}
	}

	public synchronized String strip (String messageId) {
		if (messageId != null) {
			int start = messageId.indexOf("<");
			int end = messageId.indexOf(">");
			if (start == -1) start = 0; else start++;
			if (end == -1) end = messageId.length();
			
			messageId =messageId.substring(start, end);
		} else {
			Out.print("strip " + messageId + " - null value",  Out.WARN_LEVEL);
		}
		
		return messageId; 
	}

	@Override
	public synchronized void incNumberOfNullMessageId() {
		this.numberOfNullMessageId++;
	}

	@Override
	public synchronized int getNumberOfNullMessageId() {
		return this.numberOfNullMessageId;
	}

	@Override
	public void setNumberOfNullMessageId(int value) {
		this.numberOfNullMessageId = value;
	}

	@Override
	public void addMessageFilenameMapping(String messageId, String filename) {
		if (messageId == null) {
			Out.print("addMapping " + messageId + " -> " + filename + " - null value",  Out.WARN_LEVEL);
		}
		
		if (messageIdToFilenameMapping.containsKey(messageId)) {
			Out.print("addMapping " + messageId + " -> " + filename + " - value already present",  Out.WARN_LEVEL);
		}
		
		// bug which is not a bug...
		// the mbox file contains two identical mail with messageId 5430740605062005585333c466@mail.gmail.com
		// they only differs from the "From " initial line
		messageIdToFilenameMapping.put(messageId, filename);
	}

	@Override
	public String getFilename(String messageId) {
		return getMessageIdToFilenameMapping().get(messageId);
	}

	@Override
	public Set<String> getInlineReplying() {
		return inlineReplyingSet;
	}
	
	@Override
	public Boolean isInlineReplying(String messageId) {
		return getInlineReplying().contains(messageId);
	}

	@Override
	public void setInlineReplying(String messageId) {
		if (messageId != null) {
			getInlineReplying().add(messageId);
		} else {
			Out.print("setInlineReplying " + messageId + " - attempt to set a null value",  Out.WARN_LEVEL);
		}
	}
}
