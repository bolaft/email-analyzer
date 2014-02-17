package email.alignment.model;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

import com.pwnetics.metric.Alignment;
import com.pwnetics.metric.WordSequenceAligner;
import common.util.Out;

import fr.univnantes.lina.javautil.CollectionUtilities;
import fr.univnantes.lina.mlnlp.analysis.text.simpleTokenizer.SimpleTokenizer;

/**
 * data structure which will contains the both the source and the reply message lines/sentences aligned
 * if not aligned at a given position but present in one side, will be marked null in the other side
 * 
 * several methods to align
 * 
 * @author hernandez
 */
public class MessageAlignment {

	final static String REPLY_START_PREFIX = ">";

	final static String TAG_BEGINEND = "BE";
	final static String TAG_BEGIN = "B";
	final static String TAG_END = "E";
	final static String TAG_IN = "I";
	final static String TAG_O = "O";

	final static double RATE_TO_ACCEPT_A_LINE_AS_A_REPLY_LINE = 0.5;

	private List<String> alignedReplyMessageLines; // String, String []
	private List<String> alignedSourceMessageLines; 
	
	public MessageAlignment() {
		super();
		
		setAlignedSourceMessageLines(new ArrayList<String>());
		setAlignedReplyMessageLines(new ArrayList<String>());
	}
	
	/**
	 * @return the alignedReplyMessageLines
	 */
	public List<String> getAlignedReplyMessageLines() {
		return alignedReplyMessageLines;
	}

	/**
	 * @param alignedReplyMessageLines the alignedReplyMessageLines to set
	 */
	public void setAlignedReplyMessageLines(List<String> alignedReplyMessageLines) {
		this.alignedReplyMessageLines = alignedReplyMessageLines;
	}

	/**
	 * @return the alignedSourceMessageLines
	 */
	public List<String> getAlignedSourceMessageLines() {
		return alignedSourceMessageLines;
	}

	/**
	 * @param alignedSourceMessageLines the alignedSourceMessageLines to set
	 */
	public void setAlignedSourceMessageLines(List<String> alignedSourceMessageLines) {
		this.alignedSourceMessageLines = alignedSourceMessageLines;
	}
	
	/**
	 * Align only from the reply message
	 * for each sentence of reply
	   if starts with (only one) > then assume it is a reply line and consequently it is aligned and so exists both in source and reply
	   if not exists only for reply not for the source (add null for it)
	 */
	public void alignOnlyFromReplyMessage (List<String> messageLines) {
		for (String replyMessageLine : messageLines) {
			if (replyMessageLine.startsWith(REPLY_START_PREFIX)) {
				getAlignedSourceMessageLines().add(replyMessageLine.replaceFirst("[> ]+", ""));
				getAlignedReplyMessageLines().add(replyMessageLine);
			} else {
				getAlignedSourceMessageLines().add(null);
				getAlignedReplyMessageLines().add(replyMessageLine);
			}
		}
	}
	
	/***
	 * tokenize 
	 * + align thanks to the WER measure
	 * will consider the messages as a single sequence of tokens
	 * 
	 * @param messageSourceText
	 * @param messageReplyText
	 * @return
	 */
	 public void alignBasedOnWer(String messageSourceText, String messageReplyText) {
		// tokenize source message
		List<String> tokenizedSourceMessage = new SimpleTokenizer(messageSourceText, true, true).getTokenCoveredTextList();
		String[] tokenizedSourceMessageArray = new String[tokenizedSourceMessage.size()];
		tokenizedSourceMessageArray = tokenizedSourceMessage.toArray(tokenizedSourceMessageArray);
		
		// tokenize reply message
		List<String> tokenizedReplyMessage = new SimpleTokenizer(messageReplyText, true, true).getTokenCoveredTextList();
		String[] tokenizedReplyMessageArray = new String[tokenizedReplyMessage.size()];
		tokenizedReplyMessageArray = tokenizedReplyMessage.toArray(tokenizedReplyMessageArray);

		alignBasedOnWer (tokenizedSourceMessageArray, tokenizedReplyMessageArray);
	}

	/***
	 * align thanks to the WER measure
	 * will consider the messages as a single sequence of tokens
	 * 
	 * @param tokenizedSourceMessageArray
	 * @param tokenizedReplyMessageArray
	 * @return
	 */
	 public void alignBasedOnWer(String[] tokenizedSourceMessageArray, String[] tokenizedReplyMessageArray) {
		/** Alignment */
		/* singleton object which offers a method to perform the alignment of two given sequences */ 
		WordSequenceAligner werEval = new WordSequenceAligner();

		// align a reference (source message) with an hypothesis (reply message)
		//
		// Reference words, with null elements representing insertions in the hypothesis sentence
		// and upper-cased words representing an alignment mismatch (potential reference insertions wrt to the hypothesis)
		//
		// Hypothesis words, with null elements representing deletions (missing words) in the hypothesis sentence 
		// and upper-cased words representing an alignment mismatch
		//
		// a replyMessage embeds partially/fully the sourceMessage
		// the sourceMessage does not embed at the replyMessage
		// if the replyMessage embeds partially the sourceMessage, after alignment, some part of the sourceMessage will be considered as insertions
		// if the replyMessage embeds fully the sourceMessage, after alignment, the part of the sourceMessage will be considered either as aligned or wrongly aligned
		// we cannot say anything about the part of the sourceMessage which are not present in the replyMessage 
		// for these reasons, the replyMessage should be the reference
		Alignment alignment = werEval.align(tokenizedReplyMessageArray,tokenizedSourceMessageArray);
		// As a result, a position refers to an alignment situation
		// without the null value, we can come back to the original messages (for example to get the original form without uppercase)

		/** Build an aligned source from the original source message (in order to get the original form of each token) */
		List<String> alignedTokenizedSourceMessage = new ArrayList<String>();
		int src_i = 0;
		//for (int hyp_i  = 0; hyp_i < alignment.getHypothesisLength() ; hyp_i++) {
		
		for (int hyp_i  = 0; hyp_i < (alignment.getHypothesisLength() < alignment.getReferenceLength() ? alignment.getReferenceLength(): alignment.getHypothesisLength()); hyp_i++) {
			String sourceToken = null;
			if (alignment.getHypothesis()[hyp_i] != null) { sourceToken= tokenizedSourceMessageArray[src_i++];}
			alignedTokenizedSourceMessage.add(sourceToken);
		}

		/** Index the tokens which are part of reply lines */
		Set<Integer> replyLinesTokenPositionSet = indexReplyLineTokens(
				alignment.getHypothesis(),alignment.getReference()
		);


		/** Index the token ending the sentences  */
		Set<Integer> sentenceEndingTokenPositions = indexSentenceEndings(
				alignment.getHypothesis(),alignment.getReference(), replyLinesTokenPositionSet
		);

		/** Align the sentences */
		int currentSentenceStart = 0;
		
		for (int end  : sentenceEndingTokenPositions) {
			List<String> sourceMessageSentence = new ArrayList<String>();
			List<String> replyMessageSentence = new ArrayList<String>();
			
			for (int i = currentSentenceStart ; i <= end ; i++) {
				if (i < alignment.getReferenceLength() ) replyMessageSentence.add(alignment.getReference()[i]);
				if (i < alignedTokenizedSourceMessage.size()) sourceMessageSentence.add(alignedTokenizedSourceMessage.get(i));
			}
			
			// if the end position belongs to reply lines tokens then we consider the sentence as a reply line i.e. aligned
			if (replyLinesTokenPositionSet.contains(end)) {
				getAlignedSourceMessageLines().add(CollectionUtilities.stringListToString(sourceMessageSentence, " ", false).replaceAll("[ \t\n]+", " "));
				getAlignedReplyMessageLines().add(CollectionUtilities.stringListToString(replyMessageSentence, " ", false).replaceAll("[ \t\n]+", " "));
			}
			else {
				// in order to indicate that the current lines are not aligned we set to null the reply message lines
				getAlignedSourceMessageLines().add(CollectionUtilities.stringListToString(sourceMessageSentence, " ", false).replaceAll("[ \t\n]+", " "));
				getAlignedReplyMessageLines().add(null);
				//getAlignedSourceMessageLines().add(null);
				//getAlignedReplyMessageLines().add(CollectionUtilities.stringListToString(replyMessageSentence, " ").replaceAll("[ \t\n]+", " "));

			}
			currentSentenceStart = end+1;
		}
	}

	/**
	 * 
	 * lines can be sentences or newlines separated sequences of tokens
	 * aligned lines should be at the same position in the list 
	 * when one of the line is not aligned there is null value in the other side
	 * object can stand for String or List<String> or String []
	 * 			// for each sentence of the replyMessage   
				// if the current reply line isAligned
				//		if the previous and the next reply line are not aligned then tag the current source line BE
				//		else if	the previous reply line is not aligned then tag the current source line B
				//			 	else	if the next reply line is not aligned then tag the current source line E
				// 						else (the current reply line is surrounded by aligned lines) tag the current source line I
	// Alternative
		// for each sentence r_i of the replyMessage
		// if isReplyLine(r_i) // with alignement
		//  	if (!isReplyLine(r_i-1) and !isReplyLine(r_i+1)) tag(sourceAlignedLine(r_i)) = BE
		// 		else if (!isReplyLine(r_i-1)) tag(sourceAlignedLine(r_i)) = B
		//			 else if (!isReplyLine(r_i+1)) tag(sourceAlignedLine(r_i)) = E
		//				  else  tag(sourceAlignedLine(r_i)) = I
	 * @param sourceLines
	 * @param alignedReplyMessageLines
	 */
	public static List<String> tagSourceMessage (List<?> alignedSourceMessageLines, List<?> alignedReplyMessageLines) {
		List<String> taggedSourceMessage = new ArrayList<String> ();

		// for each sentence in the reply message
		for (int i = 0 ; i < alignedReplyMessageLines.size() ; i++) {
			Boolean previousReplyLineisAligned = false;
			Boolean nextReplyLineisAligned = false;

			// if both line are aligned
			if (areAligned (alignedSourceMessageLines.get(i), alignedReplyMessageLines.get(i))) {
				if (i>0) if (areAligned (alignedSourceMessageLines.get(i-1), alignedReplyMessageLines.get(i-1))) previousReplyLineisAligned = true;
				if (i<alignedReplyMessageLines.size()-1) if  (areAligned (alignedSourceMessageLines.get(i+1), alignedReplyMessageLines.get(i+1))) nextReplyLineisAligned = true;

				if (!previousReplyLineisAligned && ! nextReplyLineisAligned)	taggedSourceMessage.add(TAG_BEGINEND);
				else if (!previousReplyLineisAligned ) taggedSourceMessage.add(TAG_BEGIN); 
				else if (!nextReplyLineisAligned ) taggedSourceMessage.add(TAG_END); 
				else taggedSourceMessage.add(TAG_IN);
			} else {
				taggedSourceMessage.add(TAG_O);
			}
		}
		
		return taggedSourceMessage;
	}

	private static Boolean areAligned(Object o1, Object o2) {
		return o1 != null &&  o2 != null;
	}

	/**
	 * @param alignment
	 * @param replyTokenPositionSet
	 * @return
	 */
	private static Set<Integer> indexSentenceEndings(
			String [] sourceAlignedMessage, String [] replyAlignedMessage, Set<Integer> replyTokenPositionSet) {
		// in non reply line, we consider each line.separator as a sentence ending
		// in reply lines, we consider the punctuationSymbolSet separator characters as sentence ending candidates

		Set<String> punctuationSymbolSet = new HashSet<String> ();
		punctuationSymbolSet.add(".");
		punctuationSymbolSet.add("?");
		punctuationSymbolSet.add("!");
		punctuationSymbolSet.add(";");
		punctuationSymbolSet.add(":");
		//punctuationSymbolSet.add(",");
		Set<Integer> endCandidatesInNonReplyLines  = new TreeSet<Integer>();
		Set<Integer> endCandidatesInReplyLines  = new TreeSet<Integer>();
		String previousTokenBis = "";
		
		// parse again the tokens of the longest message (source or reply)
		for (int ri  = 0; ri < (sourceAlignedMessage.length < replyAlignedMessage.length ? replyAlignedMessage.length : sourceAlignedMessage.length); ri++) {
			// if the current token ends a line
			if (replyAlignedMessage[ri] != null && replyAlignedMessage[ri].endsWith(System.getProperty("line.separator"))) {
				// if we are in non reply line, we consider it as a sentence ending
				if (!replyTokenPositionSet.contains(ri)) {
					endCandidatesInNonReplyLines.add(ri);
				}
			}

			// if the current token is in a reply line and belongs to the set of sentence ending tokens, we consider the position as an ending sentence 
			if (replyTokenPositionSet.contains(ri) && punctuationSymbolSet.contains(replyAlignedMessage[ri])) {
				endCandidatesInReplyLines.add(ri);
			}
			
			previousTokenBis = replyAlignedMessage[ri];
		}
		
		//  end case of previous token was not ending by a line.separator
		if (previousTokenBis == null || !previousTokenBis.endsWith(System.getProperty("line.separator"))) {
			endCandidatesInReplyLines.add((sourceAlignedMessage.length < replyAlignedMessage.length ? replyAlignedMessage.length : sourceAlignedMessage.length));
		}

		/**  Smoothing and merging endlines of endCandidatesInReplyLines and endCandidatesInNonReplyLines in the same set  */
		Set<Integer> sentenceEndingTokenPositions  = new TreeSet<Integer>(endCandidatesInNonReplyLines);
		
		for (int endCandidate : endCandidatesInReplyLines) {
			// Bug null pointer exception
			if ((endCandidate+1 <= replyAlignedMessage.length) 
					&& (replyAlignedMessage[endCandidate+1] != null 
					&& replyAlignedMessage[endCandidate+1].endsWith(System.getProperty("line.separator")))) {
				sentenceEndingTokenPositions.remove(endCandidate);
				sentenceEndingTokenPositions.add(endCandidate+1);
			} else sentenceEndingTokenPositions.add(endCandidate);
		}
		
		return sentenceEndingTokenPositions;
	}

	/**
	 * @param tokenizedReplyMessageArray
	 * @param alignment
	 * @return
	 */
	private static Set<Integer> indexReplyLineTokens(String [] sourceAlignedMessage, String [] replyAlignedMessage) {
		/* identify the offsets of words belonging to a reply line in the hypothesis (source message)*/
		// apply smoothing for not exactly lines
		Set<Integer> replyTokenPositionSet  = new HashSet<Integer>();

		/* identify the offsets of reply lines in the hypothesis (source message)*/
		//Set<Integer> replyLineStartPositionSet = new HashSet<Integer>();

		String previousToken = "";
		Boolean parsingAReplyLine = false;
		Boolean previousLineWasAReplyLine = false;

		// properties of the current line\n
		// set of positions of tokens in the current line
		Set<Integer> currentLineTokenPositionSet  = new TreeSet<Integer>();
		// set of positions of aligned tokens in the current line
		Set<Integer> currentLineAlignedTokenPositionSet  = new TreeSet<Integer>();

		// for each token (of the longest sequence hyp/ref), index...
		// getReferenceLength: Get the length of the original reference sequence. 
		// 		This is not the same as reference.length(), because that member variable may have null elements inserted to mark hypothesis insertions.
		// getHypothesisLength: Get the length of the original hypothesis sequence. 
		// 		This is not the same as hypothesis.length(), because that member variable may have null elements inserted to mark hypothesis deletions.
		// may not have the same size
		for (int ri  = 0; ri < (sourceAlignedMessage.length < replyAlignedMessage.length ? replyAlignedMessage.length : sourceAlignedMessage.length); ri++) {
			currentLineTokenPositionSet.add(ri);

			// index the position where two words are aligned (are aligned if identical)
			if (sourceAlignedMessage[ri] != null && sourceAlignedMessage[ri].equalsIgnoreCase(replyAlignedMessage[ri])) {
				currentLineAlignedTokenPositionSet.add(ri);
			}

			// index the position of the first reply token in a reply line
			// we assume that should start with REPLY_START_PREFIX and be preceded by a "line.separator"
			// bug when two successive line.separator only separated by one token... TODO fixed ? 
			if (replyAlignedMessage[ri] != null && replyAlignedMessage[ri].startsWith(REPLY_START_PREFIX)) { // && (ri == 0 || previousToken.endsWith(System.getProperty("line.separator")))) {
				if ((ri == 0)  || (previousToken != null && previousToken.endsWith(System.getProperty("line.separator")))) {
					parsingAReplyLine = true;
				}
			}
			// if is the token ending a line
			else if (replyAlignedMessage[ri] != null && replyAlignedMessage[ri].endsWith(System.getProperty("line.separator"))) {
				// determine if the current line was aligned or not, and consequently records the offsets of words as belonging to a reply line 
				// smooth the lines where a few words are not aligned (for various reasons)
				// if more than a certain percent was aligned then the line is aligned
				if (parsingAReplyLine) {
					if (((float)currentLineAlignedTokenPositionSet.size()/(float)currentLineTokenPositionSet.size()) >= RATE_TO_ACCEPT_A_LINE_AS_A_REPLY_LINE) {
						replyTokenPositionSet.addAll(currentLineTokenPositionSet);
					}
				}

				// Case of truncated lines
				// Example:
				// > fournisseur =E0 l'aide. Gr=E2ce =E0 sa collaboration, j'ai pu me connecte=
				// r =E0
				// > nouveau en cr=E9ant une nouvelle connexion et en conservant les m=EAmes
				//
				// previous line was a reply line;
				// last token of the previous sentence was "=\n" 
				//
				// not implemented: following may be a reply line...
				// not implemented: threshod on similarity rate
				// Alternatives: consider lines from the source message ; not possible since we need all the sentences of reply messages 
				else {
					int start = ri - currentLineTokenPositionSet.size()+1;
					
					if (start -2 >=0) {
						// TODO change the minimal size as a parameter
						if (previousLineWasAReplyLine && (replyAlignedMessage[start -2] != null && replyAlignedMessage[start -2].startsWith("=")) && (currentLineTokenPositionSet.size() < 10)) {
							replyTokenPositionSet.addAll(currentLineTokenPositionSet);
						}
					}
				}
				
				previousLineWasAReplyLine = parsingAReplyLine;
				parsingAReplyLine = false;
				currentLineTokenPositionSet = new TreeSet<Integer>();
				currentLineAlignedTokenPositionSet  = new TreeSet<Integer>();
			}
			
			previousToken = replyAlignedMessage[ri];
		}

		// TODO end case of previous token was not ending by a line separator
		if (parsingAReplyLine && (previousToken == null || !previousToken.endsWith(System.getProperty("line.separator")))) {
			Out.print("last token is not a line separator so the current reply line has not been processed", Out.WARN_LEVEL);			
		}
		
		return replyTokenPositionSet;
	}
}
