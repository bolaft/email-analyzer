package email.mbox.resource;

import java.util.Map;
import java.util.Set;

/**
 * Interface which models Email message box ; 
 * Declare the methods handled by the annotators to access the resource 
 */
public interface MBoxResourceInterface {

	/** Add a new message */
	public void setMessage(String messageId);
	
	/** Get the set of messages */
	public Set<String> getMessages();
	
	/** Get the set of messageId of initial thread messages */
	public Set<String> getInitialThreadMessages();

	/** Get the map which associates a message to a set of reply messages*/
	public Map<String, Set<String>> getRepliedBy();
	
	/** Get the association reply message to the message which is replied */
	public Map<String, String> getRepliesTo();
	
	/***/
	public Map<String, String> getMessageIdToFilenameMapping();

	/** Get the number of messageId with unexpected null value (due to wrong message format) */
	public int getNumberOfNullMessageId();

	/** Get the set of message Id which are assumed to be some inline replying) */
	public Set<String> getInlineReplying();
	
	
	/** Get the set of messageId of reply messages of a given one*/
	public Set<String> getMessagesIdWhichRepliesTo(String messageId);
	
	/** Get the message id of the message replied by a given message id*/
	public String getMessageIdRepliedBy(String messageId);
	
	/** Get the filename corresponding to a messageId  */
	public String getFilename(String messageId);
	
	/** based on an heuristic (at least two distinct block of reply lines)*/
	public Boolean isInlineReplying(String messageId);
	
	/** Add an association between a messageId and a filename */
	public void addMessageFilenameMapping(String messageId, String filename);
	
	/** Declare an inline replying message  */
	public void setInlineReplying(String messageId);	
	
	/** Declare an initial thread message  */
	public void setInitialThreadMessage(String messageId);

	/** Declare a couple of messageIds in repliedBy relation */
	public void setRepliedBy(String messageIdRepliedBy, String messageIdReplyTo);
	
	/** Declare a couple of messageIds in repliesTo relation */
	public void setRepliesTo(String messageIdReplyTo, String messageIdRepliedBy);
	
	/** Increment the number of messageId with unexpected null value (due to wrong message format) */
	public void incNumberOfNullMessageId();
	
	/** Increment the number of messageId with unexpected null value (due to wrong message format) */
	public void setNumberOfNullMessageId(int value);
	
	/** Return the content of the resource as a string  
	 *  @return 
	 */
	public String toString();

	/** 
	 * Save the content of the resource on the file system
	 */
	public void save(String filename);

	public String threadTreeStructureEcho(Integer i, String messageId);
}