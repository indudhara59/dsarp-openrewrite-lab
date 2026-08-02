package com.dsarp.analyzer;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collections;
import java.util.Set;
import java.util.TreeSet;

/** Minimal deterministic JVM class-file reader focused on semantically resolved type references. */
final class ClassFileParser {
    private static final int CLASS_MAGIC = 0xCAFEBABE;

    ParsedClass parse(Path classFile) throws IOException {
        try (DataInputStream input = new DataInputStream(
                new BufferedInputStream(Files.newInputStream(classFile)))) {
            if (input.readInt() != CLASS_MAGIC) {
                throw new IOException("Not a JVM class file: " + classFile);
            }
            input.readUnsignedShort();
            input.readUnsignedShort();
            ConstantPool pool = readConstantPool(input);
            int access = input.readUnsignedShort();
            int thisClass = input.readUnsignedShort();
            input.readUnsignedShort();
            Set<String> references = new TreeSet<>();
            pool.collectClassReferences(references);

            int interfaceCount = input.readUnsignedShort();
            for (int index = 0; index < interfaceCount; index++) {
                addClass(pool.className(input.readUnsignedShort()), references);
            }
            skipMembers(input, pool, references);
            int methodCount = readMembers(input, pool, references);
            readAttributes(input, pool, references);
            String className = normalize(pool.className(thisClass));
            references.remove(className);
            return new ParsedClass(className, access, methodCount,
                    Collections.unmodifiableSet(references));
        } catch (EOFException exception) {
            throw new IOException("Truncated class file: " + classFile, exception);
        }
    }

    private ConstantPool readConstantPool(DataInputStream input) throws IOException {
        int count = input.readUnsignedShort();
        Object[] entries = new Object[count];
        byte[] tags = new byte[count];
        for (int index = 1; index < count; index++) {
            int tag = input.readUnsignedByte();
            tags[index] = (byte) tag;
            switch (tag) {
                case 1 -> entries[index] = input.readUTF();
                case 3, 4 -> input.readInt();
                case 5, 6 -> {
                    input.readLong();
                    index++;
                }
                case 7, 8, 16, 19, 20 -> entries[index] = input.readUnsignedShort();
                case 9, 10, 11, 12, 17, 18 ->
                        entries[index] = new int[] {input.readUnsignedShort(), input.readUnsignedShort()};
                case 15 -> {
                    input.readUnsignedByte();
                    input.readUnsignedShort();
                }
                default -> throw new IOException("Unsupported constant-pool tag " + tag);
            }
        }
        return new ConstantPool(entries, tags);
    }

    private void skipMembers(DataInputStream input, ConstantPool pool, Set<String> references)
            throws IOException {
        readMembers(input, pool, references);
    }

    private int readMembers(DataInputStream input, ConstantPool pool, Set<String> references)
            throws IOException {
        int count = input.readUnsignedShort();
        for (int index = 0; index < count; index++) {
            input.readUnsignedShort();
            input.readUnsignedShort();
            scanTypeText(pool.utf(input.readUnsignedShort()), references);
            readAttributes(input, pool, references);
        }
        return count;
    }

    private void readAttributes(DataInputStream input, ConstantPool pool, Set<String> references)
            throws IOException {
        int count = input.readUnsignedShort();
        for (int index = 0; index < count; index++) {
            String name = pool.utf(input.readUnsignedShort());
            int length = input.readInt();
            byte[] bytes = input.readNBytes(length);
            if (bytes.length != length) {
                throw new EOFException("Truncated attribute " + name);
            }
            if ("Signature".equals(name) && length == 2) {
                int signatureIndex = ((bytes[0] & 0xff) << 8) | (bytes[1] & 0xff);
                scanTypeText(pool.utf(signatureIndex), references);
            }
        }
    }

    static void scanTypeText(String text, Set<String> destination) {
        if (text == null) {
            return;
        }
        int index = 0;
        while (index < text.length()) {
            if (text.charAt(index) != 'L') {
                index++;
                continue;
            }
            int start = index + 1;
            int end = start;
            while (end < text.length() && text.charAt(end) != ';' && text.charAt(end) != '<') {
                end++;
            }
            addClass(text.substring(start, end), destination);
            index = start;
            if (end == start) {
                index++;
            }
        }
    }

    private static void addClass(String internalName, Set<String> destination) {
        if (internalName == null || internalName.isBlank()) {
            return;
        }
        String normalized = normalize(internalName);
        if (!normalized.isBlank()) {
            destination.add(normalized);
        }
    }

    private static String normalize(String internalName) {
        String value = internalName;
        while (value.startsWith("[")) {
            value = value.substring(1);
        }
        if (value.startsWith("L") && value.endsWith(";")) {
            value = value.substring(1, value.length() - 1);
        }
        return value.replace('/', '.');
    }

    private record ConstantPool(Object[] entries, byte[] tags) {
        String utf(int index) {
            if (index <= 0 || index >= entries.length || tags[index] != 1) {
                return null;
            }
            return (String) entries[index];
        }

        String className(int index) {
            if (index <= 0 || index >= entries.length || tags[index] != 7) {
                return null;
            }
            return utf((Integer) entries[index]);
        }

        void collectClassReferences(Set<String> destination) {
            for (int index = 1; index < entries.length; index++) {
                if (tags[index] == 7) {
                    addClass(className(index), destination);
                } else if (tags[index] == 1) {
                    scanTypeText((String) entries[index], destination);
                }
            }
        }
    }
}
